import os
import secrets

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Announcement, Student, Teacher
from app.services.audit import write_audit
from app.utils.security import roles_required


announcements_bp = Blueprint("announcements_api", __name__)
ALLOWED_VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v"}


def visible_query():
    claims = get_jwt()
    role = claims.get("role")
    query = Announcement.query
    if role == "Teacher":
        teacher = Teacher.query.filter_by(user_id=int(get_jwt_identity())).first()
        teacher_id = teacher.id if teacher else -1
        return query.filter(
            db.or_(
                Announcement.audience.in_(["all", "teachers"]),
                db.and_(Announcement.audience == "teacher", Announcement.target_id == teacher_id),
            )
        )
    if role == "Parent":
        student_id = claims.get("studentId")
        return query.filter(
            db.or_(
                Announcement.audience.in_(["all", "parents"]),
                db.and_(Announcement.audience == "parent", Announcement.target_id == student_id),
            )
        )
    if role in {"Admin", "Super Admin"}:
        return query
    return query.filter(db.false())


def visible_announcements():
    return visible_query().order_by(Announcement.published_at.desc())


@announcements_bp.get("")
@jwt_required()
def list_announcements():
    items = visible_announcements().all()
    return jsonify({"items": [item.to_dict() for item in items], "total": len(items)})


@announcements_bp.get("/targets")
@jwt_required()
@roles_required("Admin", "Super Admin")
def announcement_targets():
    teachers = [
        {"id": item.id, "name": item.to_dict()["name"], "reference": item.employee_number}
        for item in Teacher.query.order_by(Teacher.last_name, Teacher.first_name).all()
    ]
    parents = [
        {"id": item.id, "name": f"Parent of {item.to_dict()['name']}", "reference": item.registration_number}
        for item in Student.query.order_by(Student.last_name, Student.first_name).all()
    ]
    return jsonify({"teachers": teachers, "parents": parents})


@announcements_bp.post("")
@jwt_required()
@roles_required("Admin", "Super Admin")
def create_announcement():
    title = (request.form.get("title") or "").strip()
    body = (request.form.get("body") or "").strip()
    audience = (request.form.get("audience") or "").strip()
    upload = request.files.get("video")
    if not title or (not body and not upload):
        return jsonify({"error": "Title and either a written message or video are required."}), 400
    if audience not in {"all", "teachers", "parents", "teacher", "parent"}:
        return jsonify({"error": "Select a valid announcement audience."}), 400

    target_id = None
    if audience in {"teacher", "parent"}:
        try:
            target_id = int(request.form.get("targetId"))
        except (TypeError, ValueError):
            return jsonify({"error": "Select a specific recipient."}), 400
        model = Teacher if audience == "teacher" else Student
        if not db.session.get(model, target_id):
            return jsonify({"error": "The selected recipient does not exist."}), 400

    video_path = video_filename = video_mime_type = None
    if upload and upload.filename:
        original = secure_filename(upload.filename)
        extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
        if extension not in ALLOWED_VIDEO_EXTENSIONS:
            return jsonify({"error": "Allowed video files: MP4, WebM, MOV, and M4V."}), 400
        upload_dir = os.path.join(current_app.instance_path, "uploads", "announcements")
        os.makedirs(upload_dir, exist_ok=True)
        stored = f"{secrets.token_hex(16)}.{extension}"
        video_path = os.path.join(upload_dir, stored)
        upload.save(video_path)
        video_filename = original
        video_mime_type = upload.mimetype

    item = Announcement(
        title=title,
        body=body,
        audience=audience,
        target_id=target_id,
        video_path=video_path,
        video_filename=video_filename,
        video_mime_type=video_mime_type,
        created_by_id=int(get_jwt_identity()),
        updated_by_id=int(get_jwt_identity()),
    )
    db.session.add(item)
    db.session.flush()
    write_audit("announcement_created", "Announcement", item.id, {"audience": audience, "targetId": target_id})
    db.session.commit()
    return jsonify({"item": item.to_dict()}), 201


@announcements_bp.get("/<int:item_id>/video")
@jwt_required()
def announcement_video(item_id):
    item = visible_query().filter(Announcement.id == item_id).first()
    if not item or not item.video_path or not os.path.isfile(item.video_path):
        return jsonify({"error": "Announcement video not found."}), 404
    return send_file(item.video_path, mimetype=item.video_mime_type, download_name=item.video_filename)


@announcements_bp.delete("/<int:item_id>")
@jwt_required()
@roles_required("Admin", "Super Admin")
def delete_announcement(item_id):
    item = db.session.get(Announcement, item_id)
    if not item:
        return jsonify({"error": "Announcement not found."}), 404
    if item.video_path and os.path.isfile(item.video_path):
        os.remove(item.video_path)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Announcement deleted."})
