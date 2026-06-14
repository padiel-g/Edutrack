from flask import Blueprint, jsonify, send_file
from flask_jwt_extended import get_jwt, jwt_required
from sqlalchemy import func

from app.extensions import db
from app.models import Attendance, Invoice, Payment, Receipt, ReportCard, Student
from app.services.pdf import simple_pdf

pdf_bp = Blueprint("pdfs", __name__)


@pdf_bp.get("/report-cards/<int:student_id>")
@jwt_required()
def report_card(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found"}), 404
    role = get_jwt().get("role")
    if role not in {"Admin", "Super Admin", "Parent"}:
        return jsonify({"error": "Report cards are not available to this portal."}), 403
    if role == "Parent" and get_jwt().get("studentId") != student_id:
        return jsonify({"error": "You can only view reports for your own child."}), 403
    query = ReportCard.query.filter_by(student_id=student_id)
    if role == "Parent":
        query = query.filter_by(status="Published")
    report = query.order_by(ReportCard.published_at.desc(), ReportCard.id.desc()).first()
    if not report:
        return jsonify({"error": "No published report card found."}), 404
    from app.routes.report_cards import report_pdf_buffer

    return send_file(
        report_pdf_buffer(report),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"{student.registration_number}-report-card.pdf",
    )


@pdf_bp.get("/receipts/<int:payment_id>")
@jwt_required()
def receipt(payment_id):
    payment = db.session.get(Payment, payment_id)
    if not payment:
        return jsonify({"error": "Payment not found"}), 404
    receipt_record = Receipt.query.filter_by(payment_id=payment_id).first()
    rows = [
        ("Payment Ref.", payment.payment_reference),
        ("Registration No.", payment.student.registration_number if payment.student else "-"),
        ("Amount", f"{float(payment.amount or 0):.2f}"),
        ("Receipt No.", receipt_record.receipt_number if receipt_record else "-"),
    ]
    return send_file(simple_pdf("EduTrack Payment Receipt", rows), mimetype="application/pdf", download_name="receipt.pdf")


@pdf_bp.get("/invoices/<int:invoice_id>")
@jwt_required()
def invoice_pdf(invoice_id):
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    rows = [
        ("Invoice No.", invoice.invoice_number),
        ("Registration No.", invoice.student.registration_number if invoice.student else "-"),
        ("Amount", f"{float(invoice.amount or 0):.2f}"),
        ("Balance", f"{float(invoice.balance or 0):.2f}"),
        ("Status", invoice.status),
    ]
    return send_file(simple_pdf("EduTrack Invoice", rows), mimetype="application/pdf", download_name="invoice.pdf")


@pdf_bp.get("/finance-report")
@jwt_required()
def finance_report():
    total_invoiced = db.session.query(func.coalesce(func.sum(Invoice.amount), 0)).scalar()
    total_paid = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()
    rows = [
        ("Total invoiced", f"{float(total_invoiced or 0):.2f}"),
        ("Total paid", f"{float(total_paid or 0):.2f}"),
        ("Outstanding", f"{float((total_invoiced or 0) - (total_paid or 0)):.2f}"),
    ]
    return send_file(simple_pdf("EduTrack Finance Report", rows), mimetype="application/pdf", download_name="finance-report.pdf")


@pdf_bp.get("/attendance-report")
@jwt_required()
def attendance_report():
    total = Attendance.query.count()
    present = Attendance.query.filter_by(status="present").count()
    absent = max(total - present, 0)
    rows = [("Total records", total), ("Present", present), ("Absent/Other", absent)]
    return send_file(simple_pdf("EduTrack Attendance Report", rows), mimetype="application/pdf", download_name="attendance-report.pdf")
