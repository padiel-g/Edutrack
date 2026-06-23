from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    AcademicYear,
    Attendance,
    ExamResult,
    FinalResult,
    Parent,
    SchoolClass,
    Student,
    StudentResult,
    Subject,
    Teacher,
    teacher_classes,
    teacher_subjects,
)
from app.services.audit import write_audit
from app.utils.security import roles_required

admin_classes_bp = Blueprint("admin_classes", __name__)


GRADE_LEVELS = [
    "ECD",
    "Grade 1",
    "Grade 2",
    "Grade 3",
    "Grade 4",
    "Grade 5",
    "Grade 6",
    "Grade 7",
    "Form 1",
    "Form 2",
    "Form 3",
    "Form 4",
    "Lower Six",
    "Upper Six",
]


def class_payload(school_class):
    subject_count = db.session.scalar(
        db.select(func.count(func.distinct(teacher_subjects.c.subject_id))).where(
            teacher_subjects.c.class_id == school_class.id
        )
    ) or len(school_class.subjects)
    teacher_count = db.session.scalar(
        db.select(func.count(func.distinct(teacher_subjects.c.teacher_id))).where(
            teacher_subjects.c.class_id == school_class.id
        )
    ) or len(school_class.assigned_teachers)
    student_count = Student.query.filter_by(class_id=school_class.id).count()
    payload = school_class.to_dict()
    payload.update(
        {
            "studentCount": student_count,
            "subjectCount": int(subject_count or 0),
            "teacherCount": int(teacher_count or 0),
            "enrollment": f"{student_count}/{school_class.capacity or 0}",
        }
    )
    return payload


def teacher_assignment_rows(class_id):
    rows = db.session.execute(
        db.select(Teacher, Subject)
        .join(teacher_subjects, teacher_subjects.c.teacher_id == Teacher.id)
        .join(Subject, Subject.id == teacher_subjects.c.subject_id)
        .where(teacher_subjects.c.class_id == class_id)
        .order_by(Teacher.last_name, Teacher.first_name, Subject.name)
    ).all()
    return [
        {
            "teacherId": teacher.id,
            "teacherName": teacher.to_dict()["name"],
            "employeeNumber": teacher.employee_number,
            "department": teacher.department,
            "email": teacher.email,
            "phone": teacher.phone,
            "subjectId": subject.id,
            "subjectCode": subject.code,
            "subjectName": subject.name,
            "subjectType": subject.stream,
        }
        for teacher, subject in rows
    ]


@admin_classes_bp.get("/classes")
@jwt_required()
@roles_required("Admin", "Super Admin")
def list_classes():
    query = SchoolClass.query
    search = (request.args.get("search") or "").strip()
    grade_level = (request.args.get("gradeLevel") or "").strip()
    stream = (request.args.get("stream") or "").strip()
    academic_year_id = request.args.get("academicYearId")
    if search:
        like = f"%{search}%"
        query = query.filter(SchoolClass.name.ilike(like))
    if grade_level:
        query = query.filter(SchoolClass.grade_level == grade_level)
    if stream:
        query = query.filter(SchoolClass.stream == stream)
    if academic_year_id:
        query = query.filter(SchoolClass.academic_year_id == int(academic_year_id))
    classes = query.order_by(SchoolClass.name).all()
    return jsonify({"items": [class_payload(item) for item in classes], "gradeLevels": GRADE_LEVELS})


@admin_classes_bp.get("/classes/<int:class_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def get_class(class_id):
    school_class = db.session.get(SchoolClass, class_id)
    if not school_class:
        return jsonify({"error": "Class not found."}), 404
    students = Student.query.filter_by(class_id=class_id).order_by(Student.last_name, Student.first_name).all()
    assignments = teacher_assignment_rows(class_id)
    subjects_by_id = {}
    for row in assignments:
        subjects_by_id[row["subjectId"]] = {
            "id": row["subjectId"],
            "code": row["subjectCode"],
            "name": row["subjectName"],
            "subjectType": row["subjectType"],
        }
    for subject in school_class.subjects:
        subjects_by_id.setdefault(
            subject.id,
            {"id": subject.id, "code": subject.code, "name": subject.name, "subjectType": subject.stream},
        )
    attendance_total = Attendance.query.filter_by(class_id=class_id).count()
    present_total = Attendance.query.filter_by(class_id=class_id, status="present").count()
    avg_score = db.session.scalar(
        db.select(func.avg(StudentResult.final_mark)).where(StudentResult.class_id == class_id)
    )
    return jsonify(
        {
            "item": class_payload(school_class),
            "students": [
                {
                    "id": student.id,
                    "registrationNumber": student.registration_number,
                    "name": student.to_dict()["name"],
                    "gender": student.gender,
                    "parent": student.primary_parent.to_dict()["name"] if student.primary_parent else None,
                    "status": student.status,
                }
                for student in students
            ],
            "subjects": sorted(subjects_by_id.values(), key=lambda item: item["name"]),
            "teachers": assignments,
            "classTeacher": school_class.class_teacher.to_dict() if school_class.class_teacher else None,
            "attendanceSummary": {
                "records": attendance_total,
                "present": present_total,
                "attendanceRate": round((present_total / attendance_total) * 100, 1) if attendance_total else None,
            },
            "performanceSummary": {
                "averageScore": round(float(avg_score), 1) if avg_score is not None else None,
                "examResultCount": ExamResult.query.filter_by(class_id=class_id).count(),
                "finalResultCount": FinalResult.query.filter_by(class_id=class_id).count(),
            },
        }
    )


@admin_classes_bp.post("/classes")
@jwt_required()
@roles_required("Admin", "Super Admin")
def create_class():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    grade_level = (data.get("gradeLevel") or data.get("grade_level") or "").strip()
    stream = (data.get("stream") or "").strip() or None
    try:
        capacity = int(data.get("capacity") or 35)
        academic_year_id = int(data["academicYearId"] or data["academic_year_id"])
        class_teacher_id = int(data["classTeacherId"]) if data.get("classTeacherId") else None
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Class name, grade/form level, capacity, and academic year are required."}), 400
    if not name or not grade_level:
        return jsonify({"error": "Class name and grade/form level are required."}), 400
    if capacity <= 0:
        return jsonify({"error": "Capacity must be greater than 0."}), 400
    if not db.session.get(AcademicYear, academic_year_id):
        return jsonify({"error": "Academic year not found."}), 404
    if class_teacher_id and not db.session.get(Teacher, class_teacher_id):
        return jsonify({"error": "Class teacher not found."}), 404
    if SchoolClass.query.filter_by(name=name, academic_year_id=academic_year_id).first():
        return jsonify({"error": "A class with this name already exists in the selected academic year."}), 409
    school_class = SchoolClass(
        name=name,
        grade_level=grade_level,
        stream=stream,
        capacity=capacity,
        academic_year_id=academic_year_id,
        teacher_id=class_teacher_id,
    )
    db.session.add(school_class)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A class with this name already exists in the selected academic year."}), 409
    write_audit("class_created", "SchoolClass", school_class.id, {"className": name})
    db.session.commit()
    return jsonify({"item": class_payload(school_class)}), 201


@admin_classes_bp.put("/classes/<int:class_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def update_class(class_id):
    school_class = db.session.get(SchoolClass, class_id)
    if not school_class:
        return jsonify({"error": "Class not found."}), 404
    data = request.get_json() or {}
    if "name" in data:
        school_class.name = (data.get("name") or "").strip()
    if "gradeLevel" in data:
        school_class.grade_level = (data.get("gradeLevel") or "").strip()
    if "stream" in data:
        school_class.stream = (data.get("stream") or "").strip() or None
    if "capacity" in data:
        school_class.capacity = int(data.get("capacity") or school_class.capacity)
    if "academicYearId" in data:
        school_class.academic_year_id = int(data["academicYearId"])
    if "classTeacherId" in data:
        teacher_id = data.get("classTeacherId")
        school_class.teacher_id = int(teacher_id) if teacher_id else None
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify({"error": "A class with this name already exists in the selected academic year."}), 409
    write_audit("class_updated", "SchoolClass", school_class.id, {"className": school_class.name})
    db.session.commit()
    return jsonify({"item": class_payload(school_class)})


@admin_classes_bp.delete("/classes/<int:class_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def delete_class(class_id):
    school_class = db.session.get(SchoolClass, class_id)
    if not school_class:
        return jsonify({"error": "Class not found."}), 404
    if Student.query.filter_by(class_id=class_id).first():
        return jsonify({"error": "This class has students assigned and cannot be deleted."}), 409
    db.session.execute(teacher_subjects.delete().where(teacher_subjects.c.class_id == class_id))
    db.session.execute(teacher_classes.delete().where(teacher_classes.c.class_id == class_id))
    school_class.subjects = []
    db.session.delete(school_class)
    write_audit("class_deleted", "SchoolClass", class_id)
    db.session.commit()
    return jsonify({"message": "Class deleted."})
