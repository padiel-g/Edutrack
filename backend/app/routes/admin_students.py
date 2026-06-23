from datetime import date

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError

from app.extensions import db, limiter
from app.models import (
    AcademicYear,
    Attendance,
    AuditLog,
    ContinuousAssessment,
    ExamResult,
    FeeReminder,
    FinalResult,
    Invoice,
    Message,
    Notification,
    Parent,
    PasswordResetCode,
    Payment,
    Receipt,
    ReportCard,
    SchoolClass,
    Student,
    StudentFeeAccount,
    StudentResult,
    StudentSubject,
    Subject,
    Submission,
    User,
)
from app.services.audit import write_audit
from app.services.numbering import next_registration_number
from app.utils.security import roles_required
from app.utils.credentials import generate_temporary_password, is_strong_password

admin_students_bp = Blueprint("admin_students", __name__)


def parse_date(value):
    return date.fromisoformat(value) if value else None


def dependency_names(checks):
    return [name for name, query in checks if query.first() is not None]


def current_academic_year_id():
    current = AcademicYear.query.filter_by(is_current=True).order_by(AcademicYear.id.desc()).first()
    if current:
        return current.id
    latest = AcademicYear.query.order_by(AcademicYear.start_date.desc(), AcademicYear.id.desc()).first()
    return latest.id if latest else None


def resolve_student_class(data):
    class_id = data.get("classId")
    class_name = (data.get("className") or "").strip()
    academic_year_id = data.get("academicYearId") or current_academic_year_id()
    if class_id:
        try:
            class_id = int(class_id)
        except (TypeError, ValueError):
            raise ValueError("Class ID must be a valid integer.")
        school_class = db.session.get(SchoolClass, class_id)
        if not school_class:
            raise LookupError("Selected class was not found.")
        return school_class
    if not class_name:
        raise ValueError("Type a class before registering the student.")
    school_class = SchoolClass.query.filter_by(name=class_name, academic_year_id=academic_year_id).first()
    if school_class:
        return school_class
    school_class = SchoolClass(
        name=class_name,
        grade_level=class_name,
        capacity=35,
        academic_year_id=academic_year_id,
    )
    db.session.add(school_class)
    db.session.flush()
    return school_class


def delete_linked_user_if_unused(user):
    if not user:
        return
    blockers = dependency_names(
        [
            ("messages", Message.query.filter((Message.sender_id == user.id) | (Message.recipient_id == user.id))),
            ("payments recorded by this account", Payment.query.filter_by(recorded_by_id=user.id)),
            ("receipts issued by this account", Receipt.query.filter_by(issued_by_id=user.id)),
            ("approved report cards", ReportCard.query.filter_by(approved_by_id=user.id)),
        ]
    )
    if blockers:
        raise ValueError(f"The linked login account still has {', '.join(blockers)} and cannot be deleted.")
    PasswordResetCode.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    Notification.query.filter_by(user_id=user.id).delete(synchronize_session=False)
    AuditLog.query.filter_by(user_id=user.id).update({"user_id": None}, synchronize_session=False)
    db.session.delete(user)


@admin_students_bp.get("/students")
@jwt_required()
@roles_required("Admin", "Super Admin")
def list_students():
    query = Student.query
    search = request.args.get("search")
    status = request.args.get("status")
    class_id = request.args.get("classId")
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Student.registration_number.ilike(like),
                Student.first_name.ilike(like),
                Student.last_name.ilike(like),
                Student.email.ilike(like),
            )
        )
    if status:
        query = query.filter_by(status=status)
    if class_id:
        query = query.filter_by(class_id=int(class_id))
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(max(int(request.args.get("perPage", 10)), 1), 100)
    pagination = query.order_by(Student.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [s.to_dict() for s in pagination.items], "total": pagination.total, "page": page, "perPage": per_page})


@admin_students_bp.post("/students")
@jwt_required()
@roles_required("Admin", "Super Admin")
@limiter.limit("30 per minute")
def create_student():
    data = request.get_json() or {}

    first_name = (data.get("firstName") or "").strip()
    last_name = (data.get("lastName") or "").strip()
    if not first_name or not last_name:
        return jsonify({"error": "First name and last name are required."}), 400

    number_of_subjects = data.get("numberOfSubjects")
    raw_subject_ids = data.get("selectedSubjectIds") or []

    try:
        school_class = resolve_student_class(data)
    except LookupError as error:
        return jsonify({"error": str(error)}), 404
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    grade_form = school_class.grade_level
    class_stream = school_class.stream or school_class.name
    try:
        number_of_subjects = int(number_of_subjects) if number_of_subjects is not None else 0
    except (TypeError, ValueError):
        return jsonify({"error": "Number of subjects must be a valid integer."}), 400
    if number_of_subjects <= 0:
        return jsonify({"error": "Number of subjects is required and must be greater than 0."}), 400
    if not isinstance(raw_subject_ids, list) or not raw_subject_ids:
        return jsonify({"error": "A student cannot be registered without selecting subjects."}), 400

    try:
        subject_ids = [int(s) for s in raw_subject_ids]
    except (TypeError, ValueError):
        return jsonify({"error": "Selected subject IDs must be integers."}), 400

    if len(subject_ids) != len(set(subject_ids)):
        return jsonify({"error": "Duplicate subjects are not allowed for the same student."}), 400
    if len(subject_ids) != number_of_subjects:
        return jsonify({"error": "Selected subjects must match the number of subjects value."}), 400

    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all()
    if len(subjects) != len(subject_ids):
        return jsonify({"error": "One or more selected subjects do not exist."}), 400

    registration_number = next_registration_number()
    student = Student(
        registration_number=registration_number,
        admission_number=registration_number,
        first_name=first_name,
        middle_name=data.get("middleName"),
        last_name=last_name,
        gender=data.get("gender"),
        date_of_birth=parse_date(data.get("dateOfBirth")),
        birth_certificate_number=(data.get("birthCertificateNumber") or "").strip() or None,
        national_id=(data.get("nationalId") or "").strip() or None,
        class_type=(data.get("classType") or "").strip() or None,
        class_id=school_class.id,
        academic_year_id=data.get("academicYearId") or school_class.academic_year_id,
        parent_id=data.get("parentId"),
        address=data.get("address"),
        phone=data.get("phone"),
        email=data.get("email"),
        enrollment_date=parse_date(data.get("enrollmentDate")) or date.today(),
        status=data.get("status", "active"),
        grade_form=grade_form,
        class_stream=class_stream,
        number_of_subjects=number_of_subjects,
    )
    parent_temporary_password = generate_temporary_password()
    student.set_parent_password(parent_temporary_password)
    student.parent_must_change_password = True
    try:
        if data.get("userId"):
            student.user_id = data["userId"]
        elif data.get("email") and data.get("password"):
            from app.models import Role

            role = Role.query.filter_by(name="Student").first()
            if not role:
                return jsonify({"error": "Student role does not exist. Create the role before creating a student login account."}), 400
            if not is_strong_password(data["password"]):
                return jsonify({"error": "Student password must be at least 10 characters and include uppercase, lowercase, number, and special character."}), 400
            user = User(email=data["email"], first_name=first_name, last_name=last_name, phone=data.get("phone"), role=role)
            user.set_password(data["password"])
            db.session.add(user)
            db.session.flush()
            student.user_id = user.id
        if student.parent_id:
            parent = db.session.get(Parent, student.parent_id)
            if parent:
                student.parents.append(parent)
        db.session.add(student)
        db.session.flush()
        for subject in subjects:
            db.session.add(StudentSubject(student_id=student.id, subject_id=subject.id))
        db.session.add(StudentFeeAccount(student_id=student.id, account_number=registration_number.replace("EDU", "FEE"), current_balance=0))
        write_audit("student_registered", "Student", student.id, {"registrationNumber": registration_number, "gradeForm": grade_form, "classStream": class_stream})
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "The student could not be registered because an email, identity number, or generated account already exists."}), 409
    except Exception:
        db.session.rollback()
        return jsonify({"error": "The student could not be registered. Check the form values and try again."}), 500
    return jsonify({
        "item": student.to_dict(),
        "registrationNumber": registration_number,
        "parentTemporaryPassword": parent_temporary_password,
    }), 201


@admin_students_bp.get("/students/<int:student_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def get_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"item": student.to_dict(), "profile": build_profile(student)})


@admin_students_bp.put("/students/<int:student_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def update_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    data = request.get_json() or {}
    mapping = {
        "firstNames": "first_names",
        "lastName": "last_name",
        "gender": "gender",
        "nationalId": "national_id",
        "classType": "class_type",
        "classId": "class_id",
        "academicYearId": "academic_year_id",
        "parentId": "parent_id",
        "address": "address",
        "phone": "phone",
        "email": "email",
        "status": "status",
    }
    for key, attr in mapping.items():
        if key in data:
            setattr(student, attr, data[key])
    if "dateOfBirth" in data:
        student.date_of_birth = parse_date(data.get("dateOfBirth"))
    if "enrollmentDate" in data:
        student.enrollment_date = parse_date(data.get("enrollmentDate")) or student.enrollment_date
    write_audit("student_updated", "Student", student.id, {"registrationNumber": student.registration_number})
    db.session.commit()
    return jsonify({"item": student.to_dict()})


@admin_students_bp.patch("/students/<int:student_id>/status")
@jwt_required()
@roles_required("Admin", "Super Admin")
def change_student_status(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    student.status = (request.get_json() or {}).get("status", "inactive")
    if student.status != "active":
        student.parent_token_version += 1
        if student.user:
            student.user.token_version += 1
    write_audit("student_status_changed", "Student", student.id, {"status": student.status})
    db.session.commit()
    return jsonify({"item": student.to_dict()})


@admin_students_bp.delete("/students/<int:student_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def delete_student(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    blockers = dependency_names(
        [
            ("attendance", Attendance.query.filter_by(student_id=student.id)),
            ("continuous assessments", ContinuousAssessment.query.filter_by(student_id=student.id)),
            ("exam results", ExamResult.query.filter_by(student_id=student.id)),
            ("final results", FinalResult.query.filter_by(student_id=student.id)),
            ("student results", StudentResult.query.filter_by(student_id=student.id)),
            ("submissions", Submission.query.filter_by(student_id=student.id)),
            ("invoices", Invoice.query.filter_by(student_id=student.id)),
            ("payments", Payment.query.filter_by(student_id=student.id)),
            ("receipts", Receipt.query.filter_by(student_id=student.id)),
            ("fee reminders", FeeReminder.query.filter_by(student_id=student.id)),
            ("report cards", ReportCard.query.filter_by(student_id=student.id)),
        ]
    )
    if blockers:
        return jsonify({"error": f"This student has {', '.join(blockers)} and cannot be deleted. Deactivate the account instead."}), 409

    user = student.user
    registration_number = student.registration_number
    try:
        student.parents.clear()
        StudentSubject.query.filter_by(student_id=student.id).delete(synchronize_session=False)
        if student.fee_account:
            db.session.delete(student.fee_account)
        db.session.delete(student)
        delete_linked_user_if_unused(user)
        write_audit("student_deleted", "Student", student_id, {"registrationNumber": registration_number})
        db.session.commit()
    except (IntegrityError, ValueError) as error:
        db.session.rollback()
        return jsonify({"error": str(error) or "This student still has records and cannot be deleted."}), 409
    return jsonify({"message": "Student account deleted."})


@admin_students_bp.get("/students/<int:student_id>/profile")
@jwt_required()
@roles_required("Admin", "Super Admin")
def student_profile(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"profile": build_profile(student)})


def build_profile(student):
    return {
        "student": student.to_dict(),
        "class": student.school_class.to_dict() if student.school_class else None,
        "academicYear": {"id": student.academic_year.id, "name": student.academic_year.name} if student.academic_year else None,
        "parent": student.primary_parent.to_dict() if student.primary_parent else None,
        "feeAccount": student.fee_account.to_dict() if student.fee_account else None,
        "invoices": [invoice.to_dict() for invoice in student.invoices],
        "payments": [payment.to_dict() for payment in student.payments],
    }


@admin_students_bp.get("/student-form-options")
@jwt_required()
@roles_required("Admin", "Super Admin")
def student_form_options():
    classes = SchoolClass.query.order_by(SchoolClass.name).all()
    return jsonify(
        {
            "classes": [item.to_dict() for item in classes],
            "academicYears": [{"id": item.id, "name": item.name} for item in AcademicYear.query.order_by(AcademicYear.name.desc()).all()],
            "parents": [item.to_dict() for item in Parent.query.order_by(Parent.id.desc()).all()],
            "subjects": [item.to_dict() for item in Subject.query.order_by(Subject.stream, Subject.name).all()],
            "gradeForms": sorted({item.grade_level for item in classes if item.grade_level}),
            "classStreams": sorted({item.stream for item in classes if item.stream}),
        }
    )
