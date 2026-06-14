from datetime import date as date_cls, datetime

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models import (
    Attendance,
    ClassRegister,
    SchoolClass,
    Student,
    Teacher,
)
from app.services.audit import write_audit
from app.utils.security import roles_required


attendance_bp = Blueprint("attendance", __name__)


VALID_STATUSES = {"Present", "Absent"}


def parse_date(value, field="date"):
    if not value:
        raise ValueError(f"{field} is required.")
    try:
        return date_cls.fromisoformat(value)
    except ValueError:
        raise ValueError(f"{field} must be in YYYY-MM-DD format.")


def current_teacher():
    return Teacher.query.filter_by(user_id=int(get_jwt_identity())).first()


def serialize_student(student):
    return {
        "id": student.id,
        "registrationNumber": student.registration_number,
        "firstName": student.first_name,
        "lastName": student.last_name,
        "name": " ".join(part for part in [student.first_name, student.middle_name, student.last_name] if part),
    }


def serialize_attendance_entry(record):
    return {
        "id": record.id,
        "studentId": record.student_id,
        "status": record.status,
        "notes": record.notes,
    }


def serialize_register(register, entries=None, roster=None):
    payload = {
        "id": register.id,
        "classId": register.class_id,
        "className": register.school_class.name if register.school_class else None,
        "teacherId": register.teacher_id,
        "teacherName": " ".join(
            part for part in [register.teacher.first_name, register.teacher.middle_name, register.teacher.last_name] if part
        ) if register.teacher else None,
        "date": register.date.isoformat(),
        "submittedAt": register.submitted_at.isoformat() if register.submitted_at else None,
        "isLocked": register.is_locked,
        "notes": register.notes,
    }
    if entries is not None:
        payload["entries"] = [serialize_attendance_entry(item) for item in entries]
    if roster is not None:
        payload["students"] = [serialize_student(item) for item in roster]
    return payload


def class_roster(class_id):
    return (
        Student.query.filter(Student.class_id == class_id, Student.status == "active")
        .order_by(Student.last_name, Student.first_name)
        .all()
    )


def managed_classes(teacher_id):
    return SchoolClass.query.filter_by(teacher_id=teacher_id).order_by(
        SchoolClass.grade_level, SchoolClass.name
    ).all()


def serialize_managed_class(school_class):
    return {
        "id": school_class.id,
        "name": school_class.name,
        "gradeLevel": school_class.grade_level,
        "studentCount": Student.query.filter_by(class_id=school_class.id, status="active").count(),
    }


# ---------------------------------------------------------------------------
# Class-teacher endpoints
# ---------------------------------------------------------------------------

@attendance_bp.get("/teacher/register/<int:class_id>")
@jwt_required()
@roles_required("Teacher")
def get_register(class_id):
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404

    school_class = db.session.get(SchoolClass, class_id)
    if not school_class:
        return jsonify({"error": "Class not found."}), 404
    if school_class.teacher_id != teacher.id:
        return jsonify({"error": "Only the assigned class teacher can mark this register."}), 403

    try:
        register_date = parse_date(request.args.get("date") or date_cls.today().isoformat())
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    register = ClassRegister.query.filter_by(class_id=class_id, date=register_date).first()
    students = class_roster(class_id)
    existing_attendance = (
        Attendance.query.filter(Attendance.class_id == class_id, Attendance.date == register_date).all()
        if students
        else []
    )

    payload = {
        "classId": class_id,
        "className": school_class.name,
        "date": register_date.isoformat(),
        "isLocked": bool(register and register.is_locked),
        "submittedAt": register.submitted_at.isoformat() if register and register.submitted_at else None,
        "students": [serialize_student(item) for item in students],
        "entries": [serialize_attendance_entry(item) for item in existing_attendance],
    }
    return jsonify(payload)


@attendance_bp.post("/teacher/register/<int:class_id>")
@jwt_required()
@roles_required("Teacher")
def save_register(class_id):
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404

    school_class = db.session.get(SchoolClass, class_id)
    if not school_class:
        return jsonify({"error": "Class not found."}), 404
    if school_class.teacher_id != teacher.id:
        return jsonify({"error": "Only the assigned class teacher can mark this register."}), 403

    data = request.get_json() or {}
    try:
        register_date = parse_date(data.get("date"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    entries = data.get("entries") or []
    if not isinstance(entries, list):
        return jsonify({"error": "entries must be a list."}), 400

    submit = bool(data.get("submit"))

    register = ClassRegister.query.filter_by(class_id=class_id, date=register_date).first()
    if register and register.is_locked:
        return jsonify({"error": "This register has been submitted and is locked."}), 409
    if register is None:
        register = ClassRegister(
            class_id=class_id,
            teacher_id=teacher.id,
            date=register_date,
        )
        db.session.add(register)
        db.session.flush()

    roster_ids = {student.id for student in class_roster(class_id)}
    seen_student_ids = set()
    for entry in entries:
        try:
            student_id = int(entry.get("studentId"))
        except (TypeError, ValueError):
            return jsonify({"error": "Each entry needs a valid studentId."}), 400
        status = (entry.get("status") or "").strip().capitalize()
        if status not in VALID_STATUSES:
            return jsonify({"error": "Status must be Present or Absent."}), 400
        if student_id not in roster_ids:
            return jsonify({"error": f"Student {student_id} is not in this class."}), 400
        if student_id in seen_student_ids:
            return jsonify({"error": f"Duplicate entry for student {student_id}."}), 400
        seen_student_ids.add(student_id)
        notes = (entry.get("notes") or "").strip() or None

        record = Attendance.query.filter_by(student_id=student_id, date=register_date).first()
        if record:
            record.status = status
            record.notes = notes
            record.class_id = class_id
            record.teacher_id = teacher.id
        else:
            db.session.add(
                Attendance(
                    student_id=student_id,
                    class_id=class_id,
                    teacher_id=teacher.id,
                    date=register_date,
                    status=status,
                    notes=notes,
                )
            )

    if submit:
        if len(seen_student_ids) < len(roster_ids):
            missing = roster_ids - seen_student_ids
            return jsonify(
                {
                    "error": "Mark every student before submitting the register.",
                    "missingStudentIds": sorted(missing),
                }
            ), 400
        register.submitted_at = datetime.utcnow()

    register.notes = (data.get("notes") or "").strip() or None
    register.teacher_id = teacher.id

    write_audit(
        "register_submitted" if submit else "register_saved",
        "ClassRegister",
        register.id,
        {
            "classId": class_id,
            "className": school_class.name,
            "date": register_date.isoformat(),
            "entryCount": len(seen_student_ids),
        },
    )
    db.session.commit()

    students = class_roster(class_id)
    existing_attendance = Attendance.query.filter(
        Attendance.class_id == class_id, Attendance.date == register_date
    ).all()
    return jsonify(
        {
            "message": "Register submitted." if submit else "Register saved.",
            "register": {
                "classId": class_id,
                "className": school_class.name,
                "date": register_date.isoformat(),
                "isLocked": register.is_locked,
                "submittedAt": register.submitted_at.isoformat() if register.submitted_at else None,
                "students": [serialize_student(item) for item in students],
                "entries": [serialize_attendance_entry(item) for item in existing_attendance],
            },
        }
    )


@attendance_bp.get("/teacher/my-classes")
@jwt_required()
@roles_required("Teacher")
def my_classes_summary():
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404
    return jsonify({"items": [serialize_managed_class(item) for item in managed_classes(teacher.id)]})


@attendance_bp.get("/teacher/my-class")
@jwt_required()
@roles_required("Teacher")
def my_class_summary():
    """Backward-compatible endpoint for clients that only support one class."""
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404
    classes = managed_classes(teacher.id)
    return jsonify({"class": serialize_managed_class(classes[0]) if classes else None})


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@attendance_bp.get("/admin/registers")
@jwt_required()
@roles_required("Admin", "Super Admin")
def list_registers():
    query = ClassRegister.query.filter(ClassRegister.submitted_at.is_not(None))
    teacher_id = request.args.get("teacherId")
    if teacher_id:
        try:
            query = query.filter(ClassRegister.teacher_id == int(teacher_id))
        except ValueError:
            return jsonify({"error": "teacherId must be an integer."}), 400
    class_id = request.args.get("classId")
    if class_id:
        try:
            query = query.filter(ClassRegister.class_id == int(class_id))
        except ValueError:
            return jsonify({"error": "classId must be an integer."}), 400
    date_str = request.args.get("date")
    if date_str:
        try:
            query = query.filter(ClassRegister.date == parse_date(date_str))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    if date_from:
        try:
            query = query.filter(ClassRegister.date >= parse_date(date_from, "from"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
    if date_to:
        try:
            query = query.filter(ClassRegister.date <= parse_date(date_to, "to"))
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400

    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("perPage", 25)), 1), 100)
    except ValueError:
        page, per_page = 1, 25

    pagination = (
        query.order_by(ClassRegister.date.desc(), ClassRegister.id.desc())
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    return jsonify(
        {
            "items": [serialize_register(item) for item in pagination.items],
            "total": pagination.total,
            "page": page,
            "perPage": per_page,
        }
    )


@attendance_bp.get("/admin/registers/<int:class_id>/<string:register_date>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def get_admin_register(class_id, register_date):
    try:
        target_date = parse_date(register_date)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    register = ClassRegister.query.filter_by(class_id=class_id, date=target_date).first()
    if not register:
        return jsonify({"error": "No register found for this class and date."}), 404
    if not register.is_locked:
        return jsonify({"error": "Register has not been submitted yet."}), 404

    entries = Attendance.query.filter(
        Attendance.class_id == class_id, Attendance.date == target_date
    ).order_by(Attendance.id).all()
    # Preserve the submitted roster even if students later change classes.
    students = sorted(
        [entry.student for entry in entries if entry.student],
        key=lambda student: (student.last_name, student.first_name),
    )
    return jsonify({"register": serialize_register(register, entries=entries, roster=students)})


# ---------------------------------------------------------------------------
# Parent endpoint
# ---------------------------------------------------------------------------

@attendance_bp.get("/parent/attendance")
@jwt_required()
def parent_attendance():
    claims = get_jwt()
    if claims.get("role") != "Parent":
        return jsonify({"error": "Parent portal only."}), 403
    student_id = claims.get("studentId")
    student = db.session.get(Student, student_id) if student_id else None
    if not student:
        return jsonify({"error": "Student not found."}), 404

    registration_number = (request.args.get("registrationNumber") or "").strip()
    if registration_number and registration_number != student.registration_number:
        return jsonify({"error": "You can only view attendance for your own child."}), 403

    query = Attendance.query.filter(Attendance.student_id == student.id)
    date_from = request.args.get("from")
    date_to = request.args.get("to")
    try:
        if date_from:
            query = query.filter(Attendance.date >= parse_date(date_from, "from"))
        if date_to:
            query = query.filter(Attendance.date <= parse_date(date_to, "to"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    records = query.order_by(Attendance.date.desc()).all()
    locked_keys = {
        (register.class_id, register.date)
        for register in ClassRegister.query.filter(
            ClassRegister.class_id.in_({record.class_id for record in records} or {0}),
            ClassRegister.submitted_at.is_not(None),
        ).all()
    }

    visible = [record for record in records if (record.class_id, record.date) in locked_keys]
    present = sum(1 for record in visible if record.status == "Present")
    absent = sum(1 for record in visible if record.status == "Absent")

    return jsonify(
        {
            "student": {
                "id": student.id,
                "registrationNumber": student.registration_number,
                "name": " ".join(part for part in [student.first_name, student.middle_name, student.last_name] if part),
                "className": student.school_class.name if student.school_class else None,
            },
            "summary": {
                "total": len(visible),
                "present": present,
                "absent": absent,
                "presentRate": round((present / len(visible)) * 100, 1) if visible else 0,
            },
            "items": [
                {
                    "date": record.date.isoformat(),
                    "status": record.status,
                    "notes": record.notes,
                    "className": record.school_class.name if record.school_class else None,
                }
                for record in visible
            ],
        }
    )
