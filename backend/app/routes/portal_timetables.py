from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.extensions import db
from app.models import ExamTimetable, SchoolClass, Student, Teacher, Timetable, teacher_classes, teacher_subjects
from app.utils.security import roles_required


portal_timetables_bp = Blueprint("portal_timetables", __name__)
DAY_ORDER = {"Monday": 1, "Tuesday": 2, "Wednesday": 3, "Thursday": 4, "Friday": 5}


def class_labels(student):
    labels = {
        student.class_type,
        student.grade_form,
        student.school_class.name if student.school_class else None,
    }
    if student.school_class and student.school_class.grade_level:
        labels.add(f"Form {student.school_class.grade_level}")
    return {label.strip().lower() for label in labels if label and label.strip()}


@portal_timetables_bp.get("")
@jwt_required()
@roles_required("Teacher", "Parent")
def view_portal_timetables():
    claims = get_jwt()
    role = claims.get("role")

    if role == "Parent":
        student = db.session.get(Student, claims.get("studentId"))
        if not student:
            return jsonify({"error": "Learner profile not found."}), 404
        learning = Timetable.query.filter(Timetable.class_id == student.class_id) if student.class_id else Timetable.query.filter(db.false())
        labels = class_labels(student)
        exams = [item for item in ExamTimetable.query.all() if item.class_type.strip().lower() in labels]
        learner = {
            "id": student.id,
            "name": student.to_dict()["name"],
            "registrationNumber": student.registration_number,
            "class": student.school_class.name if student.school_class else student.class_type,
        }
    else:
        teacher = Teacher.query.filter_by(user_id=int(get_jwt_identity())).first()
        if not teacher:
            return jsonify({"error": "Teacher profile not found."}), 404
        class_ids = set(
            db.session.execute(
                db.select(teacher_classes.c.class_id).where(teacher_classes.c.teacher_id == teacher.id)
            ).scalars()
        )
        subject_rows = db.session.execute(
            db.select(teacher_subjects.c.class_id, teacher_subjects.c.subject_id).where(
                teacher_subjects.c.teacher_id == teacher.id
            )
        ).all()
        class_ids.update(class_id for class_id, _subject_id in subject_rows if class_id)
        subject_ids = {subject_id for _class_id, subject_id in subject_rows}
        learning = Timetable.query.filter(
            db.or_(Timetable.teacher_id == teacher.id, Timetable.class_id.in_(class_ids))
        )
        labels = {
            name.strip().lower()
            for name in db.session.execute(
                db.select(SchoolClass.name).where(SchoolClass.id.in_(class_ids))
            ).scalars()
            if name and name.strip()
        }
        exams = [
            item for item in ExamTimetable.query.all()
            if item.class_type.strip().lower() in labels or item.subject_id in subject_ids
        ]
        learner = None

    learning_items = sorted(
        learning.all(),
        key=lambda item: (DAY_ORDER.get(item.day_of_week, 99), item.start_time),
    )
    exams.sort(key=lambda item: (item.exam_date, item.start_time))
    return jsonify(
        {
            "learner": learner,
            "learningTimetable": [item.to_dict() for item in learning_items],
            "examTimetable": [item.to_dict() for item in exams],
        }
    )
