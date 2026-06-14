from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models import Attendance, AuditLog, Invoice, Parent, Payment, SchoolClass, Student, Teacher
from app.routes.announcements import visible_announcements

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.get("/analytics")
@jwt_required()
def analytics():
    claims = get_jwt()
    student_id = claims.get("studentId") if claims.get("role") == "Parent" else None
    attendance_query = Attendance.query.filter_by(student_id=student_id) if student_id else Attendance.query
    invoice_query = db.session.query(func.coalesce(func.sum(Invoice.amount), 0))
    payment_query = db.session.query(func.coalesce(func.sum(Payment.amount), 0))
    if student_id:
        invoice_query = invoice_query.filter(Invoice.student_id == student_id)
        payment_query = payment_query.filter(Payment.student_id == student_id)
    total_attendance = attendance_query.count()
    present = attendance_query.filter_by(status="present").count()
    invoiced = invoice_query.scalar()
    paid = payment_query.scalar()
    announcements = visible_announcements()
    return jsonify(
        {
            "totals": {
                "students": 1 if student_id else Student.query.count(),
                "teachers": 0 if student_id else Teacher.query.count(),
                "parents": 0 if student_id else Parent.query.count(),
                "classes": 0 if student_id else SchoolClass.query.count(),
            },
            "attendance": {
                "presentRate": round((present / total_attendance) * 100, 1) if total_attendance else 0,
                "absenceRate": round(((total_attendance - present) / total_attendance) * 100, 1) if total_attendance else 0,
            },
            "finance": {
                "totalInvoiced": float(invoiced),
                "totalPaid": float(paid),
                "outstandingBalance": float(invoiced - paid),
                "collectionRate": round((float(paid) / float(invoiced)) * 100, 1) if invoiced else 0,
            },
            "recentAnnouncements": [{"title": a.title, "audience": a.audience} for a in announcements.limit(5)],
            "recentAuditLogs": [] if student_id else [{"action": a.action, "entity": a.entity_type} for a in AuditLog.query.order_by(AuditLog.id.desc()).limit(5)],
        }
    )
