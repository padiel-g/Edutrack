import secrets
import string
from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import Role, SchoolClass, Subject, Teacher, User, teacher_classes, teacher_subjects
from app.services.audit import write_audit
from app.utils.security import roles_required

admin_teachers_bp = Blueprint("admin_teachers", __name__)


def parse_date(value):
    return date.fromisoformat(value) if value else None


def temporary_password(length=14):
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    while True:
        password = "".join(secrets.choice(alphabet) for _ in range(length))
        if (
            any(char.isupper() for char in password)
            and any(char.islower() for char in password)
            and any(char.isdigit() for char in password)
            and any(char in "!@#$%&*" for char in password)
        ):
            return password


def next_employee_number():
    latest = Teacher.query.order_by(Teacher.id.desc()).first()
    return f"TCH-{(latest.id + 1 if latest else 1):05d}"


def assignment_ids(data):
    try:
        subject_ids = list(dict.fromkeys(int(item) for item in (data.get("subjectIds") or [])))
        class_ids = list(dict.fromkeys(int(item) for item in (data.get("classIds") or [])))
    except (TypeError, ValueError):
        raise ValueError("Subject and class IDs must be integers.")
    return subject_ids, class_ids


def replace_assignments(teacher, subject_ids, class_ids):
    previous = [
        {"id": subject.id, "code": subject.code, "name": subject.name}
        for subject in sorted(teacher.subjects, key=lambda item: item.name)
    ]
    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all() if subject_ids else []
    classes = SchoolClass.query.filter(SchoolClass.id.in_(class_ids)).all() if class_ids else []
    if len(subjects) != len(subject_ids):
        raise ValueError("One or more selected subjects do not exist.")
    if len(classes) != len(class_ids):
        raise ValueError("One or more selected classes do not exist.")

    # Manage the association rows through SQL only. Mixing a manual DELETE with
    # relationship assignment makes SQLAlchemy try to delete the same rows twice.
    db.session.execute(teacher_subjects.delete().where(teacher_subjects.c.teacher_id == teacher.id))
    if classes:
        for subject in subjects:
            for school_class in classes:
                db.session.execute(
                    teacher_subjects.insert().values(
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        class_id=school_class.id,
                    )
                )
    else:
        for subject in subjects:
            db.session.execute(
                teacher_subjects.insert().values(
                    teacher_id=teacher.id,
                    subject_id=subject.id,
                    class_id=None,
                )
            )

    # Persist class assignments independently of subjects so the relationship
    # holds even before a subject has been assigned.
    previous_class_ids = set(
        db.session.scalars(
            db.select(teacher_classes.c.class_id).where(teacher_classes.c.teacher_id == teacher.id)
        )
    )
    wanted_class_ids = {school_class.id for school_class in classes}
    removed_class_ids = previous_class_ids - wanted_class_ids

    # If a class is no longer taught by this teacher, they can no longer be its
    # class teacher. Clear the designation so a class never references a teacher
    # who doesn't teach it (mirrors the dedicated set_teacher_classes endpoint).
    if removed_class_ids:
        SchoolClass.query.filter(
            SchoolClass.id.in_(removed_class_ids), SchoolClass.teacher_id == teacher.id
        ).update({SchoolClass.teacher_id: None}, synchronize_session=False)

    db.session.execute(teacher_classes.delete().where(teacher_classes.c.teacher_id == teacher.id))
    for school_class in classes:
        db.session.execute(
            teacher_classes.insert().values(
                teacher_id=teacher.id,
                class_id=school_class.id,
            )
        )

    db.session.expire(teacher, ["subjects", "assigned_classes"])
    return (
        previous,
        [{"id": subject.id, "code": subject.code, "name": subject.name} for subject in sorted(subjects, key=lambda item: item.name)],
        sorted(previous_class_ids),
        sorted(wanted_class_ids),
    )


@admin_teachers_bp.get("/teachers")
@jwt_required()
@roles_required("Admin", "Super Admin")
def list_teachers():
    query = Teacher.query.join(Teacher.user)
    search = (request.args.get("search") or "").strip()
    status = (request.args.get("status") or "").strip()
    department = (request.args.get("department") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Teacher.employee_number.ilike(like),
                Teacher.first_name.ilike(like),
                Teacher.last_name.ilike(like),
                Teacher.email.ilike(like),
            )
        )
    if status:
        query = query.filter(User.status == status)
    if department:
        query = query.filter(Teacher.department == department)
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("perPage", 25)), 1), 100)
    except ValueError:
        page, per_page = 1, 25
    pagination = query.order_by(Teacher.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [item.to_dict() for item in pagination.items], "total": pagination.total, "page": page, "perPage": per_page})


@admin_teachers_bp.post("/teachers")
@jwt_required()
@roles_required("Admin", "Super Admin")
@limiter.limit("20 per hour")
def create_teacher():
    data = request.get_json() or {}
    first_name = (data.get("firstName") or "").strip()
    last_name = (data.get("lastName") or "").strip()
    email = (data.get("email") or "").strip().lower()
    if not first_name or not last_name or not email:
        return jsonify({"error": "First name, last name, and email are required."}), 400
    if User.query.filter_by(email=email).first() or Teacher.query.filter_by(email=email).first():
        return jsonify({"error": "Email already exists."}), 409
    if data.get("nationalId") and Teacher.query.filter_by(national_id=data["nationalId"].strip()).first():
        return jsonify({"error": "National ID already exists."}), 409

    role = Role.query.filter_by(name="Teacher").first()
    if not role:
        return jsonify({"error": "Teacher role does not exist."}), 400
    try:
        subject_ids, class_ids = assignment_ids(data)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    password = temporary_password()
    creator_id = int(get_jwt_identity())
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        phone=(data.get("phone") or "").strip() or None,
        role=role,
        status="Active",
        is_active=True,
        must_change_password=True,
        created_by_id=creator_id,
        updated_by_id=creator_id,
    )
    user.set_password(password)
    try:
        teacher = Teacher(
            user=user,
            employee_number=(data.get("employeeNumber") or "").strip() or next_employee_number(),
            first_name=first_name,
            middle_name=(data.get("middleName") or "").strip() or None,
            last_name=last_name,
            gender=(data.get("gender") or "").strip() or None,
            national_id=(data.get("nationalId") or "").strip() or None,
            phone=(data.get("phone") or "").strip() or None,
            email=email,
            address=(data.get("address") or "").strip() or None,
            qualification=(data.get("qualification") or "").strip() or None,
            department=(data.get("department") or "").strip() or None,
            specialization=(data.get("specialization") or "").strip() or None,
            hire_date=parse_date(data.get("hireDate")),
            employment_status=(data.get("employmentStatus") or "Active").strip(),
            created_by_id=creator_id,
            updated_by_id=creator_id,
        )
    except ValueError:
        return jsonify({"error": "Hire date must be a valid date."}), 400
    try:
        db.session.add(teacher)
        db.session.flush()
        _, assigned, _, assigned_class_ids = replace_assignments(teacher, subject_ids, class_ids)
        write_audit(
            "teacher_account_created",
            "Teacher",
            teacher.id,
            {
                "email": email,
                "employeeNumber": teacher.employee_number,
                "assignedSubjects": assigned,
                "assignedClassIds": assigned_class_ids,
            },
        )
        db.session.commit()
    except ValueError as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "Teacher details conflict with an existing record."}), 409
    return jsonify({"item": teacher.to_dict(), "temporaryPassword": password}), 201


@admin_teachers_bp.get("/teachers/<int:teacher_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def get_teacher(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found."}), 404
    return jsonify({"item": teacher.to_dict()})


@admin_teachers_bp.put("/teachers/<int:teacher_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def update_teacher(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found."}), 404
    data = request.get_json() or {}
    try:
        subject_ids, class_ids = assignment_ids(data)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    fields = {
        "firstName": "first_name", "middleName": "middle_name", "lastName": "last_name",
        "gender": "gender", "nationalId": "national_id", "phone": "phone", "email": "email",
        "address": "address", "qualification": "qualification", "department": "department",
        "specialization": "specialization", "employmentStatus": "employment_status",
    }
    for key, field in fields.items():
        if key in data:
            value = data[key].strip() if isinstance(data[key], str) else data[key]
            setattr(teacher, field, value or None)
    try:
        if "hireDate" in data:
            teacher.hire_date = parse_date(data.get("hireDate"))
    except ValueError:
        return jsonify({"error": "Hire date must be a valid date."}), 400
    teacher.updated_by_id = int(get_jwt_identity())
    teacher.user.first_name = teacher.first_name
    teacher.user.last_name = teacher.last_name
    teacher.user.email = teacher.email
    teacher.user.phone = teacher.phone
    try:
        previous, current, previous_class_ids, current_class_ids = replace_assignments(
            teacher, subject_ids, class_ids
        )
        write_audit(
            "teacher_profile_updated",
            "Teacher",
            teacher.id,
            {
                "subjectChanges": {"before": previous, "after": current},
                "classChanges": {"before": previous_class_ids, "after": current_class_ids},
                "changedBy": "Admin",
            },
        )
        db.session.commit()
    except (ValueError, IntegrityError) as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 400
    return jsonify({"item": teacher.to_dict()})


@admin_teachers_bp.patch("/teachers/<int:teacher_id>/status")
@jwt_required()
@roles_required("Admin", "Super Admin")
def update_teacher_status(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found."}), 404
    status = (request.get_json() or {}).get("status")
    if status not in {"Active", "Inactive", "Suspended"}:
        return jsonify({"error": "Status must be Active, Inactive, or Suspended."}), 400
    previous = teacher.user.status
    teacher.user.status = status
    teacher.user.is_active = status == "Active"
    if status != "Active":
        teacher.user.token_version += 1
    teacher.employment_status = status
    action = "teacher_account_reactivated" if status == "Active" else "teacher_account_suspended"
    write_audit(action, "Teacher", teacher.id, {"from": previous, "to": status})
    db.session.commit()
    return jsonify({"item": teacher.to_dict()})


@admin_teachers_bp.delete("/teachers/<int:teacher_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def delete_teacher(teacher_id):
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found."}), 404
    teacher.user.status = "Inactive"
    teacher.user.is_active = False
    teacher.user.token_version += 1
    teacher.employment_status = "Inactive"
    write_audit("teacher_account_deactivated", "Teacher", teacher.id)
    db.session.commit()
    return jsonify({"message": "Teacher account deactivated.", "item": teacher.to_dict()})


@admin_teachers_bp.get("/teacher-form-options")
@jwt_required()
@roles_required("Admin", "Super Admin")
def teacher_form_options():
    return jsonify(
        {
            "subjects": [item.to_dict() for item in Subject.query.order_by(Subject.name).all()],
            "classes": [{"id": item.id, "name": item.name} for item in SchoolClass.query.order_by(SchoolClass.name).all()],
        }
    )


@admin_teachers_bp.put("/classes/<int:class_id>/class-teacher")
@jwt_required()
@roles_required("Admin", "Super Admin")
def assign_class_teacher(class_id):
    school_class = db.session.get(SchoolClass, class_id)
    if not school_class:
        return jsonify({"error": "Class not found."}), 404
    data = request.get_json() or {}
    teacher_id = data.get("teacherId")
    previous_id = school_class.teacher_id
    if teacher_id is None:
        school_class.teacher_id = None
        write_audit(
            "class_teacher_unassigned",
            "SchoolClass",
            school_class.id,
            {"className": school_class.name, "previousTeacherId": previous_id},
        )
        db.session.commit()
        return jsonify({"item": school_class.to_dict()})
    try:
        teacher_id = int(teacher_id)
    except (TypeError, ValueError):
        return jsonify({"error": "teacherId must be an integer."}), 400
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found."}), 404
    school_class.teacher_id = teacher.id
    # Designating a class teacher implies that teacher also teaches this class —
    # ensure the assignment exists in teacher_classes (no subject required).
    already_assigned = db.session.execute(
        db.select(teacher_classes.c.teacher_id).where(
            teacher_classes.c.teacher_id == teacher.id,
            teacher_classes.c.class_id == school_class.id,
        )
    ).first()
    if not already_assigned:
        db.session.execute(
            teacher_classes.insert().values(teacher_id=teacher.id, class_id=school_class.id)
        )
    write_audit(
        "class_teacher_assigned",
        "SchoolClass",
        school_class.id,
        {
            "className": school_class.name,
            "previousTeacherId": previous_id,
            "newTeacherId": teacher.id,
            "teacherName": " ".join(part for part in [teacher.first_name, teacher.middle_name, teacher.last_name] if part),
        },
    )
    db.session.commit()
    return jsonify({"item": school_class.to_dict()})


@admin_teachers_bp.put("/classes/<int:class_id>/teachers")
@jwt_required()
@roles_required("Admin", "Super Admin")
def set_class_teachers(class_id):
    """Assign the teaching staff for one class without changing other classes."""
    school_class = db.session.get(SchoolClass, class_id)
    if not school_class:
        return jsonify({"error": "Class not found."}), 404
    raw_ids = (request.get_json() or {}).get("teacherIds")
    if not isinstance(raw_ids, list):
        return jsonify({"error": "teacherIds must be a list."}), 400
    try:
        teacher_ids = list(dict.fromkeys(int(item) for item in raw_ids))
    except (TypeError, ValueError):
        return jsonify({"error": "Teacher IDs must be integers."}), 400

    teachers = Teacher.query.filter(Teacher.id.in_(teacher_ids)).all() if teacher_ids else []
    if len(teachers) != len(teacher_ids):
        return jsonify({"error": "One or more selected teachers do not exist."}), 400
    if school_class.teacher_id and school_class.teacher_id not in teacher_ids:
        return jsonify({"error": "The Class Teacher must also be assigned to teach this class."}), 400

    previous_ids = set(
        db.session.scalars(
            db.select(teacher_classes.c.teacher_id).where(teacher_classes.c.class_id == school_class.id)
        )
    )
    wanted_ids = set(teacher_ids)
    removed_ids = previous_ids - wanted_ids

    db.session.execute(teacher_classes.delete().where(teacher_classes.c.class_id == school_class.id))
    for teacher_id in teacher_ids:
        db.session.execute(
            teacher_classes.insert().values(teacher_id=teacher_id, class_id=school_class.id)
        )
    if removed_ids:
        db.session.execute(
            teacher_subjects.delete().where(
                teacher_subjects.c.class_id == school_class.id,
                teacher_subjects.c.teacher_id.in_(removed_ids),
            )
        )

    write_audit(
        "class_teachers_updated",
        "SchoolClass",
        school_class.id,
        {"className": school_class.name, "before": sorted(previous_ids), "after": sorted(wanted_ids)},
    )
    db.session.commit()
    return jsonify(
        {
            "item": school_class.to_dict(),
            "teachers": [teacher.to_dict() for teacher in sorted(teachers, key=lambda item: item.last_name)],
        }
    )


@admin_teachers_bp.put("/teachers/<int:teacher_id>/classes")
@jwt_required()
@roles_required("Admin", "Super Admin")
def set_teacher_classes(teacher_id):
    """Assign one or more classes to a teacher. Classes the teacher will teach.

    Independent of subjects. If the teacher is currently the class teacher of a
    class being removed, the class-teacher designation on that class is cleared.
    """
    teacher = db.session.get(Teacher, teacher_id)
    if not teacher:
        return jsonify({"error": "Teacher not found."}), 404
    data = request.get_json() or {}
    raw_ids = data.get("classIds")
    if not isinstance(raw_ids, list):
        return jsonify({"error": "classIds must be a list."}), 400
    try:
        wanted_ids = list(dict.fromkeys(int(item) for item in raw_ids))
    except (TypeError, ValueError):
        return jsonify({"error": "Class IDs must be integers."}), 400

    classes = SchoolClass.query.filter(SchoolClass.id.in_(wanted_ids)).all() if wanted_ids else []
    if len(classes) != len(wanted_ids):
        return jsonify({"error": "One or more selected classes do not exist."}), 400

    previous_ids = set(
        db.session.scalars(
            db.select(teacher_classes.c.class_id).where(teacher_classes.c.teacher_id == teacher.id)
        )
    )
    wanted_set = set(wanted_ids)
    removed_ids = previous_ids - wanted_set

    # If the teacher was a class teacher of any removed class, clear it.
    if removed_ids:
        SchoolClass.query.filter(
            SchoolClass.id.in_(removed_ids), SchoolClass.teacher_id == teacher.id
        ).update({SchoolClass.teacher_id: None}, synchronize_session=False)

    db.session.execute(teacher_classes.delete().where(teacher_classes.c.teacher_id == teacher.id))
    for class_id in wanted_ids:
        db.session.execute(
            teacher_classes.insert().values(teacher_id=teacher.id, class_id=class_id)
        )

    # Drop teacher_subjects rows tied to removed classes (those teaching links no
    # longer apply); rows with NULL class_id are untouched.
    if removed_ids:
        db.session.execute(
            teacher_subjects.delete().where(
                teacher_subjects.c.teacher_id == teacher.id,
                teacher_subjects.c.class_id.in_(removed_ids),
            )
        )

    db.session.expire(teacher, ["assigned_classes"])
    write_audit(
        "teacher_classes_updated",
        "Teacher",
        teacher.id,
        {
            "employeeNumber": teacher.employee_number,
            "before": sorted(previous_ids),
            "after": sorted(wanted_ids),
            "clearedClassTeacherOn": sorted(removed_ids),
        },
    )
    db.session.commit()
    return jsonify({"item": teacher.to_dict()})
