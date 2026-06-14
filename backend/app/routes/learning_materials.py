import os
import secrets

from flask import Blueprint, current_app, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from werkzeug.utils import secure_filename

from app.extensions import db, limiter
from app.models import LearningMaterial, Student, Subject, Teacher
from app.services.audit import write_audit
from app.utils.security import roles_required


learning_materials_bp = Blueprint("learning_materials_api", __name__)

ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "ppt", "pptx", "txt"}


def current_teacher():
    return Teacher.query.filter_by(user_id=int(get_jwt_identity())).first()


def teacher_subject(teacher, subject_id):
    try:
        subject_id = int(subject_id)
    except (TypeError, ValueError):
        return None
    return next((subject for subject in teacher.subjects if subject.id == subject_id), None)


@learning_materials_bp.get("")
@jwt_required()
def list_materials():
    claims = get_jwt()
    query = LearningMaterial.query
    assigned_subjects = []
    if claims.get("role") == "Teacher":
        teacher = current_teacher()
        if not teacher:
            return jsonify({"error": "Teacher profile not found."}), 404
        query = query.filter_by(teacher_id=teacher.id)
        assigned_subjects = [
            subject.to_dict()
            for subject in sorted(teacher.subjects, key=lambda item: item.name)
        ]
    elif claims.get("role") == "Student":
        student = Student.query.filter_by(user_id=int(get_jwt_identity())).first()
        if not student:
            return jsonify({"error": "Student profile not found."}), 404
        subject_ids = [link.subject_id for link in student.student_subjects]
        query = query.filter(LearningMaterial.subject_id.in_(subject_ids))
    elif claims.get("role") == "Parent":
        student = db.session.get(Student, claims.get("studentId"))
        subject_ids = [link.subject_id for link in student.student_subjects] if student else []
        query = query.filter(LearningMaterial.subject_id.in_(subject_ids))
    elif claims.get("role") not in {"Admin", "Super Admin"}:
        return jsonify({"error": "Learning materials are not available for this account."}), 403

    subject_id = request.args.get("subjectId")
    if subject_id:
        query = query.filter_by(subject_id=subject_id)
    items = query.order_by(LearningMaterial.id.desc()).all()
    return jsonify(
        {
            "items": [item.to_dict() for item in items],
            "total": len(items),
            "assignedSubjects": assigned_subjects,
        }
    )


@learning_materials_bp.post("")
@jwt_required()
@roles_required("Teacher")
@limiter.limit("30 per hour")
def upload_material():
    teacher = current_teacher()
    if not teacher:
        return jsonify({"error": "Teacher profile not found."}), 404
    title = (request.form.get("title") or "").strip()
    description = (request.form.get("description") or "").strip() or None
    subject = teacher_subject(teacher, request.form.get("subjectId"))
    upload = request.files.get("file")
    if not title or not subject or not upload or not upload.filename:
        return jsonify({"error": "Title, assigned subject, and file are required."}), 400

    original = secure_filename(upload.filename)
    extension = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if extension not in ALLOWED_EXTENSIONS:
        return jsonify({"error": "Allowed files: PDF, Word, PowerPoint, and TXT."}), 400

    upload_dir = current_app.config["MATERIAL_UPLOAD_PATH"]
    os.makedirs(upload_dir, exist_ok=True)
    stored = f"{secrets.token_hex(16)}.{extension}"
    full_path = os.path.join(upload_dir, stored)
    upload.save(full_path)
    size = os.path.getsize(full_path)

    material = LearningMaterial(
        title=title,
        description=description,
        file_url=full_path,
        stored_filename=stored,
        original_filename=original,
        mime_type=upload.mimetype,
        file_size=size,
        subject_id=subject.id,
        teacher_id=teacher.id,
        created_by_id=int(get_jwt_identity()),
        updated_by_id=int(get_jwt_identity()),
    )
    db.session.add(material)
    db.session.flush()
    write_audit(
        "learning_material_uploaded",
        "LearningMaterial",
        material.id,
        {"title": title, "subjectId": subject.id, "filename": original},
    )
    db.session.commit()
    return jsonify({"item": material.to_dict()}), 201


@learning_materials_bp.get("/<int:material_id>/download")
@jwt_required()
def download_material(material_id):
    material = db.session.get(LearningMaterial, material_id)
    if not material:
        return jsonify({"error": "Learning material not found."}), 404
    claims = get_jwt()
    allowed = claims.get("role") in {"Admin", "Super Admin"}
    if claims.get("role") == "Teacher":
        teacher = current_teacher()
        allowed = bool(teacher and material.teacher_id == teacher.id)
    elif claims.get("role") == "Student":
        student = Student.query.filter_by(user_id=int(get_jwt_identity())).first()
        allowed = bool(student and material.subject_id in {link.subject_id for link in student.student_subjects})
    elif claims.get("role") == "Parent":
        student = db.session.get(Student, claims.get("studentId"))
        allowed = bool(student and material.subject_id in {link.subject_id for link in student.student_subjects})
    if not allowed or not os.path.isfile(material.file_url):
        return jsonify({"error": "Learning material not found."}), 404
    return send_file(
        material.file_url,
        as_attachment=True,
        download_name=material.original_filename or material.stored_filename,
        mimetype=material.mime_type,
    )


@learning_materials_bp.delete("/<int:material_id>")
@jwt_required()
@roles_required("Teacher")
def delete_material(material_id):
    teacher = current_teacher()
    material = db.session.get(LearningMaterial, material_id)
    if not teacher or not material or material.teacher_id != teacher.id:
        return jsonify({"error": "Learning material not found."}), 404
    if os.path.isfile(material.file_url):
        os.remove(material.file_url)
    write_audit("learning_material_deleted", "LearningMaterial", material.id, {"title": material.title})
    db.session.delete(material)
    db.session.commit()
    return jsonify({"message": "Learning material deleted."})
