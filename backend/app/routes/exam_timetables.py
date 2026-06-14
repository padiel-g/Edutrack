from datetime import date, time

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models import ExamTimetable, Subject
from app.services.audit import write_audit
from app.utils.security import roles_required

exam_timetables_bp = Blueprint("exam_timetables", __name__)


def parse_time(value):
    return time.fromisoformat(value) if value else None


@exam_timetables_bp.get("")
@jwt_required()
@roles_required("Admin", "Super Admin", "Teacher", "Parent")
def list_exam_timetables():
    query = ExamTimetable.query
    class_type = (request.args.get("classType") or "").strip()
    if class_type:
        query = query.filter(ExamTimetable.class_type.ilike(f"%{class_type}%"))
    items = query.order_by(ExamTimetable.exam_date, ExamTimetable.start_time).all()
    return jsonify({"items": [item.to_dict() for item in items]})


@exam_timetables_bp.post("")
@jwt_required()
@roles_required("Admin", "Super Admin")
def create_exam_timetable():
    data = request.get_json() or {}
    class_type = (data.get("classType") or "").strip()
    if not class_type:
        return jsonify({"error": "Class type is required."}), 400

    subject = db.session.get(Subject, data.get("subjectId"))
    if not subject:
        return jsonify({"error": "Select a valid subject."}), 400

    try:
        exam_date = date.fromisoformat(data.get("examDate"))
        start_time = parse_time(data.get("startTime"))
        end_time = parse_time(data.get("endTime"))
    except (TypeError, ValueError):
        return jsonify({"error": "Enter a valid exam date and time."}), 400
    if not start_time or not end_time or end_time <= start_time:
        return jsonify({"error": "End time must be after start time."}), 400

    conflict = ExamTimetable.query.filter_by(
        exam_date=exam_date,
        class_type=class_type,
        start_time=start_time,
    ).first()
    if conflict:
        return jsonify({"error": "An exam already starts at this time for the selected class type."}), 409

    item = ExamTimetable(
        exam_date=exam_date,
        class_type=class_type,
        subject=subject,
        start_time=start_time,
        end_time=end_time,
        venue=(data.get("venue") or "").strip() or None,
        paper=(data.get("paper") or "").strip() or None,
        notes=(data.get("notes") or "").strip() or None,
    )
    db.session.add(item)
    db.session.flush()
    write_audit("exam_timetable_created", "ExamTimetable", item.id, {"classType": class_type, "subjectId": subject.id})
    db.session.commit()
    return jsonify({"item": item.to_dict()}), 201


@exam_timetables_bp.delete("/<int:item_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def delete_exam_timetable(item_id):
    item = db.session.get(ExamTimetable, item_id)
    if not item:
        return jsonify({"error": "Exam timetable entry not found."}), 404
    write_audit("exam_timetable_deleted", "ExamTimetable", item.id, {"classType": item.class_type})
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Exam timetable entry deleted."})
