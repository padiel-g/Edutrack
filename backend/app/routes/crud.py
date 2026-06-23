from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload

from app.extensions import db
from app.services.audit import write_audit
from app.utils.security import roles_required
from app.utils.credentials import is_strong_password
from app.models import (
    AcademicYear,
    Announcement,
    Assignment,
    Attendance,
    AuditLog,
    ContinuousAssessment,
    ExamResult,
    FinalResult,
    FeeReminder,
    FeeStructure,
    Invoice,
    InvoiceItem,
    LearningMaterial,
    Message,
    Notification,
    Parent,
    Payment,
    Permission,
    Receipt,
    ReportCard,
    Role,
    SchoolClass,
    SchoolSetting,
    Student,
    StudentFeeAccount,
    StudentSubject,
    Subject,
    Submission,
    Teacher,
    Term,
    Timetable,
    User,
    teacher_classes,
    teacher_subjects,
)

crud_bp = Blueprint("crud", __name__)

RESOURCES = {
    "users": User,
    "roles": Role,
    "permissions": Permission,
    "students": Student,
    "parents": Parent,
    "teachers": Teacher,
    "classes": SchoolClass,
    "subjects": Subject,
    "academic-years": AcademicYear,
    "terms": Term,
    "timetables": Timetable,
    "attendance": Attendance,
    "continuous-assessments": ContinuousAssessment,
    "exam-results": ExamResult,
    "final-results": FinalResult,
    "assignments": Assignment,
    "submissions": Submission,
    "learning-materials": LearningMaterial,
    "invoices": Invoice,
    "invoice-items": InvoiceItem,
    "student-fee-accounts": StudentFeeAccount,
    "fee-structures": FeeStructure,
    "payments": Payment,
    "receipts": Receipt,
    "fee-reminders": FeeReminder,
    "announcements": Announcement,
    "messages": Message,
    "notifications": Notification,
    "report-cards": ReportCard,
    "audit-logs": AuditLog,
    "settings": SchoolSetting,
}

ADMIN_ROLES = {"Admin", "Super Admin"}
FINANCE_ROLES = ADMIN_ROLES | {"Accounts Officer"}
READ_ROLES = {
    "users": ADMIN_ROLES,
    "roles": ADMIN_ROLES,
    "permissions": ADMIN_ROLES,
    "students": ADMIN_ROLES | {"Teacher", "Parent", "Student", "Accounts Officer"},
    "parents": ADMIN_ROLES,
    "teachers": ADMIN_ROLES | {"Teacher"},
    "classes": ADMIN_ROLES | {"Teacher", "Parent", "Student", "Accounts Officer"},
    "subjects": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "academic-years": ADMIN_ROLES | {"Teacher", "Parent", "Student", "Accounts Officer"},
    "terms": ADMIN_ROLES | {"Teacher", "Parent", "Student", "Accounts Officer"},
    "timetables": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "attendance": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "continuous-assessments": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "exam-results": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "final-results": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "assignments": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "submissions": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "learning-materials": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "invoices": FINANCE_ROLES | {"Parent", "Student"},
    "invoice-items": FINANCE_ROLES,
    "student-fee-accounts": FINANCE_ROLES | {"Parent", "Student"},
    "fee-structures": FINANCE_ROLES,
    "payments": FINANCE_ROLES | {"Parent", "Student"},
    "receipts": FINANCE_ROLES | {"Parent", "Student"},
    "fee-reminders": FINANCE_ROLES,
    "announcements": ADMIN_ROLES | {"Teacher", "Parent", "Student"},
    "messages": ADMIN_ROLES | {"Teacher", "Student"},
    "notifications": ADMIN_ROLES | {"Teacher", "Student"},
    "report-cards": ADMIN_ROLES | {"Parent"},
    "audit-logs": ADMIN_ROLES,
    "settings": FINANCE_ROLES,
}

PROTECTED_WRITE_FIELDS = {
    "id",
    "password_hash",
    "parent_password_hash",
    "created_at",
    "updated_at",
    "created_by_id",
    "updated_by_id",
    "role_id",
    "passwordHash",
    "parentPasswordHash",
    "createdAt",
    "updatedAt",
    "createdById",
    "updatedById",
    "roleId",
}

WRITABLE_FIELDS = {
    "roles": {"name", "description"},
    "permissions": {"name", "description"},
    "students": {
        "user_id", "registration_number", "admission_number", "first_name", "middle_name",
        "last_name", "date_of_birth", "gender", "birth_certificate_number", "national_id",
        "address", "phone", "email", "class_id", "class_type", "academic_year_id",
        "parent_id", "enrollment_date", "status", "grade_form", "class_stream",
        "number_of_subjects",
    },
    "parents": {"user_id", "occupation", "relationship"},
    "classes": {
        "name", "gradeLevel", "stream", "academicYearId", "capacity", "classTeacherId", "subjectIds",
        "teacherIds", "teacherSubjectAssignments", "manualSubjects",
    },
    "subjects": {"code", "name", "stream"},
    "academic-years": {"name", "start_date", "end_date", "is_current"},
    "terms": {"name", "academic_year_id", "start_date", "end_date", "is_current"},
    "timetables": {"class_id", "subject_id", "teacher_id", "day_of_week", "start_time", "end_time"},
    "attendance": {"student_id", "class_id", "teacher_id", "date", "status", "notes"},
    "continuous-assessments": {
        "student_id", "subject_id", "class_id", "term_id", "academic_year_id",
        "title", "score", "max_score",
    },
    "exam-results": {
        "student_id", "subject_id", "class_id", "term_id", "academic_year_id",
        "score", "grade", "teacher_comment",
    },
    "final-results": {
        "student_id", "class_id", "term_id", "academic_year_id", "average_score",
        "position", "status",
    },
    "assignments": {"title", "description", "class_id", "subject_id", "teacher_id", "due_date"},
    "submissions": {"assignment_id", "student_id", "file_url", "score", "feedback", "submitted_at"},
    "learning-materials": {
        "title", "description", "file_url", "stored_filename", "original_filename",
        "mime_type", "file_size", "class_id", "subject_id", "teacher_id",
    },
    "invoices": {
        "invoice_number", "student_id", "fee_account_id", "term_id", "academic_year_id",
        "issue_date", "amount", "paid_amount", "balance", "due_date", "status",
    },
    "invoice-items": {"invoice_id", "description", "quantity", "unit_amount", "total_amount"},
    "student-fee-accounts": {
        "student_id", "account_number", "term_id", "total_fee", "total_paid",
        "opening_balance", "current_balance", "status",
    },
    "fee-structures": {"class_id", "academic_year_id", "term_id", "name", "amount", "is_active"},
    "payments": {
        "payment_reference", "invoice_id", "student_id", "fee_account_id", "term_id",
        "term_name", "amount", "method", "reference_number", "note", "previous_balance",
        "new_balance", "recorded_by_id", "paid_at",
    },
    "receipts": {
        "receipt_number", "payment_id", "student_id", "amount", "issued_at",
        "pdf_url", "issued_by_id",
    },
    "fee-reminders": {"student_id", "invoice_id", "message", "channel", "status", "sent_at"},
    "announcements": {"title", "body", "audience", "target_id", "published_at"},
    "messages": {"sender_id", "recipient_id", "subject", "body", "read_at"},
    "notifications": {"user_id", "title", "body", "type", "read_at"},
    "report-cards": {"student_id", "term_id", "academic_year_id", "pdf_url", "status"},
    "settings": {"key", "value"},
    "users": {"email", "first_name", "last_name", "phone", "is_active", "status", "must_change_password", "password"},
}


def can_read_resource(resource, role):
    return role in READ_ROLES.get(resource, set())


def validate_write_payload(resource, data):
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object."
    forbidden = sorted(PROTECTED_WRITE_FIELDS.intersection(data))
    if forbidden:
        return None, f"Protected fields cannot be written: {', '.join(forbidden)}."
    allowed = WRITABLE_FIELDS.get(resource)
    if allowed is None:
        return None, "This resource cannot be changed through the generic endpoint."
    unknown = sorted(set(data) - allowed)
    if unknown:
        return None, f"Unsupported fields: {', '.join(unknown)}."
    return {key: data[key] for key in allowed if key in data}, None


def current_student_id(claims):
    if claims.get("role") == "Parent":
        return claims.get("studentId")
    if claims.get("role") == "Student":
        identity = get_jwt_identity()
        student = Student.query.filter_by(user_id=int(identity)).first() if identity and str(identity).isdigit() else None
        return student.id if student else None
    return None


def teacher_scope():
    identity = get_jwt_identity()
    teacher = Teacher.query.filter_by(user_id=int(identity)).first() if identity and str(identity).isdigit() else None
    if not teacher:
        return None, set(), set()
    class_ids = {row.id for row in teacher.assigned_classes}
    subject_rows = db.session.execute(
        db.select(teacher_subjects.c.class_id, teacher_subjects.c.subject_id)
        .where(teacher_subjects.c.teacher_id == teacher.id)
    ).all()
    class_ids.update(row.class_id for row in subject_rows if row.class_id)
    subject_ids = {row.subject_id for row in subject_rows}
    return teacher, class_ids, subject_ids


def scope_query(query, model, resource, claims):
    role = claims.get("role")
    if role in ADMIN_ROLES:
        return query
    if role == "Accounts Officer":
        return query
    if role in {"Parent", "Student"}:
        student_id = current_student_id(claims)
        if not student_id:
            return query.filter(db.false())
        student = db.session.get(Student, student_id)
        if resource == "students":
            return query.filter(Student.id == student_id)
        if resource == "classes":
            return query.filter(SchoolClass.id == (student.class_id if student else None))
        if resource == "subjects":
            return query.join(StudentSubject, StudentSubject.subject_id == Subject.id).filter(StudentSubject.student_id == student_id)
        if resource == "timetables":
            return query.filter(Timetable.class_id == (student.class_id if student else None))
        if resource == "assignments":
            return query.filter(Assignment.class_id == (student.class_id if student else None))
        if resource == "learning-materials":
            subject_ids = db.select(StudentSubject.subject_id).where(StudentSubject.student_id == student_id)
            return query.filter(LearningMaterial.subject_id.in_(subject_ids))
        if resource == "report-cards":
            return query.filter(ReportCard.student_id == student_id, ReportCard.status == "Published")
        if resource == "announcements":
            audience = "parents" if role == "Parent" else "students"
            singular = "parent" if role == "Parent" else "student"
            return query.filter(
                db.or_(
                    Announcement.audience.in_(["all", audience]),
                    db.and_(Announcement.audience == singular, Announcement.target_id == student_id),
                )
            )
        if resource == "messages" and role == "Student":
            user_id = int(get_jwt_identity())
            return query.filter(db.or_(Message.sender_id == user_id, Message.recipient_id == user_id))
        if resource == "notifications" and role == "Student":
            return query.filter(Notification.user_id == int(get_jwt_identity()))
        if hasattr(model, "student_id"):
            return query.filter(model.student_id == student_id)
        return query
    if role == "Teacher":
        teacher, class_ids, subject_ids = teacher_scope()
        if not teacher:
            return query.filter(db.false())
        if resource == "teachers":
            return query.filter(Teacher.id == teacher.id)
        if resource == "students":
            return query.filter(Student.class_id.in_(class_ids))
        if resource == "classes":
            return query.filter(SchoolClass.id.in_(class_ids))
        if resource == "subjects":
            return query.filter(Subject.id.in_(subject_ids))
        if resource == "submissions":
            return query.join(Assignment, Submission.assignment_id == Assignment.id).filter(Assignment.teacher_id == teacher.id)
        if resource == "announcements":
            return query.filter(
                db.or_(
                    Announcement.audience.in_(["all", "teachers"]),
                    db.and_(Announcement.audience == "teacher", Announcement.target_id == teacher.id),
                )
            )
        if resource == "messages":
            return query.filter(db.or_(Message.sender_id == teacher.user_id, Message.recipient_id == teacher.user_id))
        if resource == "notifications":
            return query.filter(Notification.user_id == teacher.user_id)
        if hasattr(model, "teacher_id"):
            return query.filter(model.teacher_id == teacher.id)
        if hasattr(model, "class_id"):
            query = query.filter(model.class_id.in_(class_ids))
        if hasattr(model, "subject_id"):
            query = query.filter(model.subject_id.in_(subject_ids))
        return query
    return query.filter(db.false())


def eager_load(query, resource):
    if resource == "students":
        return query.options(
            joinedload(Student.school_class),
            selectinload(Student.student_subjects).joinedload(StudentSubject.subject),
        )
    if resource == "classes":
        return query.options(
            joinedload(SchoolClass.class_teacher),
            selectinload(SchoolClass.subjects),
            selectinload(SchoolClass.assigned_teachers),
        )
    if resource == "teachers":
        return query.options(
            joinedload(Teacher.user),
            selectinload(Teacher.subjects),
            selectinload(Teacher.assigned_classes),
            selectinload(Teacher.class_teacher_classes),
        )
    return query


def serialize(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    output = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        output[column.name] = value.isoformat() if hasattr(value, "isoformat") else value
    return output


def pagination_args():
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("perPage", 25)), 1), 100)
    except ValueError:
        return 1, 25
    return page, per_page


def apply_list_filters(query, model, resource):
    search = (request.args.get("search") or "").strip()
    fee_accounts_joined = False
    if search:
        like = f"%{search}%"
        if resource == "users":
            query = query.filter(or_(User.email.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like)))
        elif resource == "teachers":
            query = query.join(Teacher.user).filter(
                or_(Teacher.employee_number.ilike(like), Teacher.department.ilike(like), User.first_name.ilike(like), User.last_name.ilike(like), User.email.ilike(like))
            )
        elif resource == "parents":
            query = query.join(Parent.user).filter(
                or_(User.first_name.ilike(like), User.last_name.ilike(like), User.email.ilike(like), Parent.occupation.ilike(like))
            )
        elif resource == "students":
            query = query.filter(
                or_(Student.registration_number.ilike(like), Student.first_name.ilike(like), Student.last_name.ilike(like), Student.email.ilike(like))
            )
        elif resource == "student-fee-accounts":
            query = query.join(Student, StudentFeeAccount.student_id == Student.id).filter(
                or_(
                    StudentFeeAccount.account_number.ilike(like),
                    Student.registration_number.ilike(like),
                    Student.first_name.ilike(like),
                    Student.last_name.ilike(like),
                )
            )
            fee_accounts_joined = True
        elif resource == "report-cards":
            query = query.join(Student, ReportCard.student_id == Student.id).filter(
                or_(Student.registration_number.ilike(like), Student.first_name.ilike(like), Student.last_name.ilike(like), ReportCard.status.ilike(like))
            )
        elif hasattr(model, "name"):
            query = query.filter(model.name.ilike(like))

    status = (request.args.get("status") or "").strip()
    if status and hasattr(model, "status"):
        query = query.filter(model.status == status)
    class_id = request.args.get("classId")
    if class_id:
        if resource == "student-fee-accounts":
            if not fee_accounts_joined:
                query = query.join(Student, StudentFeeAccount.student_id == Student.id)
                fee_accounts_joined = True
            query = query.filter(Student.class_id == int(class_id))
        elif hasattr(model, "class_id"):
            query = query.filter(model.class_id == int(class_id))
    grade_form = (request.args.get("gradeForm") or "").strip()
    class_stream = (request.args.get("classStream") or "").strip()
    if resource == "student-fee-accounts" and (grade_form or class_stream):
        if not fee_accounts_joined:
            query = query.join(Student, StudentFeeAccount.student_id == Student.id)
        if grade_form:
            query = query.filter(Student.grade_form == grade_form)
        if class_stream:
            query = query.filter(Student.class_stream == class_stream)
    student_id = request.args.get("studentId")
    if student_id and hasattr(model, "student_id"):
        query = query.filter(model.student_id == int(student_id))
    role = (request.args.get("role") or "").strip()
    if role and resource == "users":
        query = query.join(User.role).filter(Role.name == role)
    return query


@crud_bp.get("/<resource>")
@jwt_required()
def list_resource(resource):
    model = RESOURCES.get(resource)
    if not model:
        return jsonify({"error": "Unknown resource"}), 404
    claims = get_jwt()
    role = claims.get("role")
    if not can_read_resource(resource, role):
        return jsonify({"error": "Forbidden"}), 403
    page, per_page = pagination_args()
    query = eager_load(model.query, resource)
    query = scope_query(query, model, resource, claims)
    query = apply_list_filters(query, model, resource)
    pagination = query.order_by(model.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return jsonify({"items": [serialize(item) for item in pagination.items], "total": pagination.total, "page": page, "perPage": per_page})


@crud_bp.post("/<resource>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def create_resource(resource):
    if get_jwt().get("role") == "Parent":
        return jsonify({"error": "Parent portal access is read-only"}), 403
    model = RESOURCES.get(resource)
    if not model:
        return jsonify({"error": "Unknown resource"}), 404
    if resource == "teachers":
        return jsonify({"error": "Teacher accounts must be created through the secure admin teacher endpoint."}), 400
    data = request.get_json() or {}
    data, error = validate_write_payload(resource, data)
    if error:
        return jsonify({"error": error}), 400
    if resource == "users":
        return jsonify({"error": "User accounts must be created through the secure account registration endpoints."}), 400
    if resource == "classes":
        return create_class(data)
    if resource == "subjects":
        name = (data.get("name") or "").strip()
        code = (data.get("code") or "").strip().upper()
        if not name or not code:
            return jsonify({"error": "Subject name and code are required."}), 400
        if Subject.query.filter_by(code=code).first():
            return jsonify({"error": f"Subject code {code} already exists."}), 409
        data = {**data, "name": name, "code": code, "stream": (data.get("stream") or "").strip() or None}
    obj = model()
    for field, value in data.items():
        setattr(obj, field, value)
    db.session.add(obj)
    if resource == "users":
        write_audit("user_created", "User", None, {"email": data.get("email"), "roleId": data.get("role_id")})
    db.session.commit()
    return jsonify({"item": serialize(obj)}), 201


def create_class(data):
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "Class name is required."}), 400

    grade_level = (data.get("gradeLevel") or "").strip()
    if not grade_level:
        return jsonify({"error": "Grade/Form level is required."}), 400
    try:
        capacity = int(data.get("capacity") or 35)
        academic_year_id = int(data["academicYearId"]) if data.get("academicYearId") else None
    except (TypeError, ValueError):
        return jsonify({"error": "Capacity and academic year must use valid values."}), 400
    if capacity <= 0:
        return jsonify({"error": "Capacity must be greater than 0."}), 400
    if SchoolClass.query.filter_by(name=name, academic_year_id=academic_year_id).first():
        return jsonify({"error": "A class with this name already exists in the selected academic year."}), 409

    subject_ids = data.get("subjectIds") or []
    if not isinstance(subject_ids, list):
        return jsonify({"error": "subjectIds must be a list."}), 400
    try:
        subject_ids = list(dict.fromkeys(int(subject_id) for subject_id in subject_ids))
    except (TypeError, ValueError):
        return jsonify({"error": "Subject IDs must be integers."}), 400

    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all() if subject_ids else []
    if len(subjects) != len(subject_ids):
        return jsonify({"error": "One or more selected subjects do not exist."}), 400

    teacher_ids = data.get("teacherIds") or []
    if not isinstance(teacher_ids, list):
        return jsonify({"error": "teacherIds must be a list."}), 400
    try:
        teacher_ids = list(dict.fromkeys(int(teacher_id) for teacher_id in teacher_ids))
        class_teacher_id = int(data["classTeacherId"]) if data.get("classTeacherId") else None
    except (TypeError, ValueError):
        return jsonify({"error": "Teacher IDs must be integers."}), 400
    if class_teacher_id and class_teacher_id not in teacher_ids:
        teacher_ids.append(class_teacher_id)
    teachers = Teacher.query.filter(Teacher.id.in_(teacher_ids)).all() if teacher_ids else []
    if len(teachers) != len(teacher_ids):
        return jsonify({"error": "One or more selected teachers do not exist."}), 400

    raw_assignments = data.get("teacherSubjectAssignments") or []
    if not isinstance(raw_assignments, list):
        return jsonify({"error": "teacherSubjectAssignments must be a list."}), 400
    assignments = []
    for assignment in raw_assignments:
        try:
            teacher_id = int(assignment.get("teacherId"))
            assigned_subject_ids = list(dict.fromkeys(int(item) for item in (assignment.get("subjectIds") or [])))
        except (AttributeError, TypeError, ValueError):
            return jsonify({"error": "Teacher and subject assignments must use valid IDs."}), 400
        if teacher_id not in teacher_ids:
            return jsonify({"error": "A subject assignment contains a teacher who is not assigned to this class."}), 400
        if any(subject_id not in subject_ids for subject_id in assigned_subject_ids):
            return jsonify({"error": "Teachers can only be assigned subjects selected for this class."}), 400
        assignments.extend((teacher_id, subject_id) for subject_id in assigned_subject_ids)

    manual_subjects = data.get("manualSubjects") or []
    if not isinstance(manual_subjects, list):
        return jsonify({"error": "manualSubjects must be a list."}), 400

    for item in manual_subjects:
        subject_name = (item.get("name") or "").strip()
        subject_code = (item.get("code") or "").strip().upper()
        stream = (item.get("stream") or "").strip() or None
        if not subject_name or not subject_code:
            return jsonify({"error": "Each manually added subject needs a name and code."}), 400
        if Subject.query.filter_by(code=subject_code).first():
            return jsonify({"error": f"Subject code {subject_code} already exists."}), 409
        subject = Subject(name=subject_name, code=subject_code, stream=stream)
        db.session.add(subject)
        subjects.append(subject)

    school_class = SchoolClass(
        name=name,
        grade_level=grade_level,
        capacity=capacity,
        stream=(data.get("stream") or "").strip() or None,
        academic_year_id=academic_year_id,
        teacher_id=class_teacher_id,
        subjects=subjects,
    )
    db.session.add(school_class)
    db.session.flush()
    for teacher_id in teacher_ids:
        db.session.execute(
            teacher_classes.insert().values(teacher_id=teacher_id, class_id=school_class.id)
        )
    for teacher_id, subject_id in assignments:
        db.session.execute(
            teacher_subjects.insert().values(
                teacher_id=teacher_id,
                subject_id=subject_id,
                class_id=school_class.id,
            )
        )
    write_audit(
        "class_created",
        "SchoolClass",
        school_class.id,
        {
            "className": school_class.name,
            "teacherIds": teacher_ids,
            "classTeacherId": class_teacher_id,
        },
    )
    db.session.commit()
    return jsonify({"item": school_class.to_dict()}), 201


@crud_bp.get("/<resource>/<int:item_id>")
@jwt_required()
def get_resource(resource, item_id):
    model = RESOURCES.get(resource)
    if not model:
        return jsonify({"error": "Unknown resource"}), 404
    claims = get_jwt()
    role = claims.get("role")
    if not can_read_resource(resource, role):
        return jsonify({"error": "Forbidden"}), 403
    query = eager_load(model.query, resource)
    query = scope_query(query, model, resource, claims)
    obj = query.filter(model.id == item_id).first()
    if not obj:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"item": serialize(obj)})


@crud_bp.put("/<resource>/<int:item_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def update_resource(resource, item_id):
    if get_jwt().get("role") == "Parent":
        return jsonify({"error": "Parent portal access is read-only"}), 403
    model = RESOURCES.get(resource)
    if resource == "teachers":
        return jsonify({"error": "Teacher accounts must be updated through the secure admin teacher endpoint."}), 400
    obj = db.session.get(model, item_id) if model else None
    if not obj:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json() or {}
    data, error = validate_write_payload(resource, data)
    if error:
        return jsonify({"error": error}), 400
    password = data.pop("password", None)
    was_active = bool(obj.is_active and obj.status == "Active") if resource == "users" else None
    for field, value in data.items():
        setattr(obj, field, value)
    if resource == "users" and password is not None:
        if not is_strong_password(password):
            return jsonify({"error": "Password must be at least 10 characters and include uppercase, lowercase, number, and special character."}), 400
        obj.set_password(password)
        obj.must_change_password = True
        obj.token_version += 1
    if resource == "users" and was_active and (not obj.is_active or obj.status != "Active"):
        obj.token_version += 1
    write_audit(f"{resource.rstrip('s')}_updated", model.__name__, obj.id)
    db.session.commit()
    return jsonify({"item": serialize(obj)})


@crud_bp.delete("/<resource>/<int:item_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def delete_resource(resource, item_id):
    if get_jwt().get("role") == "Parent":
        return jsonify({"error": "Parent portal access is read-only"}), 403
    model = RESOURCES.get(resource)
    if resource == "teachers":
        return jsonify({"error": "Teacher accounts must be deactivated through the secure admin teacher endpoint."}), 400
    obj = db.session.get(model, item_id) if model else None
    if not obj:
        return jsonify({"error": "Not found"}), 404
    if resource == "parents":
        parent_user = obj.user
        for student in Student.query.filter_by(parent_id=obj.id).all():
            student.parent_id = None
            student.parent_token_version += 1
        obj.children.clear()
        if parent_user:
            parent_user.is_active = False
            parent_user.status = "Inactive"
            parent_user.token_version += 1
    write_audit(f"{resource.rstrip('s')}_deleted", model.__name__, obj.id)
    db.session.delete(obj)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if resource == "subjects":
            return jsonify({"error": "This subject is still assigned to school records and cannot be deleted."}), 409
        if resource == "classes":
            return jsonify({"error": "This class still has students, timetable entries, attendance, or other school records and cannot be deleted."}), 409
        if resource == "academic-years":
            return jsonify({"error": "This academic year is still used by terms, students, invoices, results, or other school records and cannot be deleted."}), 409
        return jsonify({"error": "This record is still in use and cannot be deleted."}), 409
    return jsonify({"message": "Deleted"})
