from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db, limiter
from app.models import SchoolClass, Subject, Teacher, teacher_classes, teacher_subjects
from app.services.audit import write_audit
from app.utils.security import roles_required


teacher_subjects_bp = Blueprint("teacher_subjects_api", __name__)


def current_teacher():
    return Teacher.query.filter_by(user_id=int(get_jwt_identity())).first()


def subject_summary(subjects):
    return [{"id": subject.id, "code": subject.code, "name": subject.name} for subject in subjects]


@teacher_subjects_bp.get("/classes")
@jwt_required()
@roles_required("Teacher")
def get_my_classes():
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404

    classes = (
        db.session.execute(
            db.select(SchoolClass)
            .join(teacher_classes, teacher_classes.c.class_id == SchoolClass.id)
            .where(teacher_classes.c.teacher_id == teacher.id)
            .order_by(SchoolClass.grade_level, SchoolClass.name)
        )
        .scalars()
        .all()
    )
    subject_rows = db.session.execute(
        db.select(teacher_subjects.c.class_id, Subject)
        .join(Subject, Subject.id == teacher_subjects.c.subject_id)
        .where(
            teacher_subjects.c.teacher_id == teacher.id,
            teacher_subjects.c.class_id.is_not(None),
        )
        .order_by(Subject.name)
    ).all()
    subjects_by_class = {}
    for class_id, subject in subject_rows:
        subjects_by_class.setdefault(class_id, []).append(subject_summary([subject])[0])

    return jsonify(
        {
            "teacher": {
                "id": teacher.id,
                "employeeNumber": teacher.employee_number,
                "name": teacher.to_dict()["name"],
            },
            "items": [
                {
                    "id": school_class.id,
                    "name": school_class.name,
                    "gradeLevel": school_class.grade_level,
                    "capacity": school_class.capacity,
                    "studentCount": len(school_class.students),
                    "isClassTeacher": school_class.teacher_id == teacher.id,
                    "subjects": subjects_by_class.get(school_class.id, []),
                }
                for school_class in classes
            ],
        }
    )


@teacher_subjects_bp.get("/subjects")
@jwt_required()
@roles_required("Teacher")
def get_my_subjects():
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404

    class_rows = db.session.execute(
        db.select(SchoolClass.id, SchoolClass.name)
        .join(teacher_classes, teacher_classes.c.class_id == SchoolClass.id)
        .where(teacher_classes.c.teacher_id == teacher.id)
        .order_by(SchoolClass.name)
    ).all()
    return jsonify(
        {
            "teacher": {
                "id": teacher.id,
                "employeeNumber": teacher.employee_number,
                "name": teacher.to_dict()["name"],
            },
            "assignedSubjects": subject_summary(sorted(teacher.subjects, key=lambda item: item.name)),
            "availableSubjects": subject_summary(Subject.query.order_by(Subject.name).all()),
            "assignedClasses": [{"id": row.id, "name": row.name} for row in class_rows],
        }
    )


@teacher_subjects_bp.put("/subjects")
@jwt_required()
@roles_required("Teacher")
@limiter.limit("20 per hour")
def update_my_subjects():
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404

    data = request.get_json() or {}
    if not isinstance(data.get("subjectIds"), list):
        return jsonify({"error": "subjectIds must be a list."}), 400
    try:
        subject_ids = list(dict.fromkeys(int(item) for item in data["subjectIds"]))
    except (TypeError, ValueError):
        return jsonify({"error": "Subject IDs must be integers."}), 400

    subjects = Subject.query.filter(Subject.id.in_(subject_ids)).all() if subject_ids else []
    if len(subjects) != len(subject_ids):
        return jsonify({"error": "One or more selected subjects do not exist."}), 400

    previous = subject_summary(sorted(teacher.subjects, key=lambda item: item.name))
    teacher_name = " ".join(
        part for part in [teacher.first_name, teacher.middle_name, teacher.last_name] if part
    )
    class_ids = list(
        db.session.scalars(
            db.select(teacher_classes.c.class_id).where(teacher_classes.c.teacher_id == teacher.id)
        )
    )

    db.session.execute(teacher_subjects.delete().where(teacher_subjects.c.teacher_id == teacher.id))
    if class_ids:
        for subject in subjects:
            for class_id in class_ids:
                db.session.execute(
                    teacher_subjects.insert().values(
                        teacher_id=teacher.id,
                        subject_id=subject.id,
                        class_id=class_id,
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

    current = subject_summary(sorted(subjects, key=lambda item: item.name))
    write_audit(
        "teacher_subjects_updated",
        "Teacher",
        teacher.id,
        {
            "employeeNumber": teacher.employee_number,
            "teacherName": teacher_name,
            "before": previous,
            "after": current,
            "changedBy": "Teacher",
        },
    )
    db.session.commit()
    return jsonify({"message": "Teaching subjects updated.", "assignedSubjects": current})
