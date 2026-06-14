from datetime import date, datetime, time
from decimal import Decimal, InvalidOperation
from io import BytesIO

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import func, or_, text

from app.extensions import db, limiter
from app.models import Payment, Receipt, SchoolSetting, Student, StudentFeeAccount, Term, User
from app.services.audit import write_audit
from app.services.numbering import next_receipt_number
from app.utils.security import roles_required

accounts_payments_bp = Blueprint("accounts_payments", __name__)
parent_payments_bp = Blueprint("parent_payments", __name__)
admin_payments_bp = Blueprint("admin_payments", __name__)


def decimal_money(value):
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None


def current_term():
    return Term.query.filter_by(is_current=True).order_by(Term.id.desc()).first()


def term_dict(term):
    return {
        "id": term.id,
        "name": term.name,
        "academicYear": term.academic_year.name if term.academic_year else None,
        "isCurrent": term.is_current,
    }


def guardian_name(student):
    parent = student.primary_parent or (student.parents[0] if student.parents else None)
    return parent.to_dict()["name"] if parent else "Not assigned"


def account_status(account):
    if Decimal(account.current_balance or 0) == 0 and Decimal(account.total_paid or 0) > 0:
        return "Paid"
    if Decimal(account.total_paid or 0) > 0:
        return "Partially Paid"
    return "Unpaid"


def student_summary(student):
    account = student.fee_account
    term = account.term if account and account.term else current_term()
    return {
        "id": student.id,
        "registrationNumber": student.registration_number,
        "name": student.to_dict()["name"],
        "form": student.grade_form,
        "class": student.school_class.name if student.school_class else student.grade_form,
        "stream": student.class_stream,
        "guardian": guardian_name(student),
        "currentBalance": float(account.current_balance or 0) if account else 0,
        "totalFee": float(account.total_fee or 0) if account else 0,
        "totalPaid": float(account.total_paid or 0) if account else 0,
        "status": account_status(account) if account else "Unpaid",
        "currentTerm": term_dict(term) if term else None,
    }


def payment_with_receipt(payment):
    receipt = Receipt.query.filter_by(payment_id=payment.id).first()
    return {**payment.to_dict(), "receipt": receipt.to_dict() if receipt else None}


def visible_student(student_id):
    claims = get_jwt()
    role = claims.get("role")
    if role in {"Admin", "Super Admin", "Accounts Officer"}:
        return db.session.get(Student, student_id)
    if role == "Parent":
        return db.session.get(Student, student_id) if claims.get("studentId") == student_id else None
    if role == "Student":
        student = Student.query.filter_by(user_id=int(get_jwt_identity())).first()
        return student if student and student.id == student_id else None
    return None


@accounts_payments_bp.get("/students/search")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def search_student():
    registration = (request.args.get("reg_number") or "").strip()
    name = (request.args.get("name") or "").strip()
    query = Student.query.filter(Student.status == "active")
    if registration:
        student = query.filter(func.lower(Student.registration_number) == registration.lower()).first()
        if not student:
            return jsonify({"error": "No student exists with that registration number."}), 404
        return jsonify({"student": student_summary(student), "terms": [term_dict(item) for item in Term.query.order_by(Term.start_date.desc()).all()]})
    if name:
        like = f"%{name}%"
        students = query.filter(or_(Student.first_name.ilike(like), Student.last_name.ilike(like))).limit(20).all()
        return jsonify({"items": [student_summary(item) for item in students]})
    return jsonify({"error": "Enter a registration number or student name."}), 400


@accounts_payments_bp.post("/payments")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
@limiter.limit("30 per minute")
def create_payment():
    data = request.get_json() or {}
    registration = (data.get("registrationNumber") or "").strip()
    amount = decimal_money(data.get("amount"))
    total_fee = decimal_money(data.get("totalFee")) if data.get("totalFee") not in (None, "") else None
    if not registration:
        return jsonify({"error": "Student registration number is required."}), 400
    if amount is None or amount <= 0:
        return jsonify({"error": "Amount paid must be greater than 0."}), 400

    student = Student.query.filter(func.lower(Student.registration_number) == registration.lower()).first()
    if not student:
        return jsonify({"error": "No student exists with that registration number."}), 404
    term_name = (data.get("termName") or "").strip()
    term = db.session.get(Term, data.get("termId")) if data.get("termId") else None
    if not term_name and term:
        term_name = term.name
    if not term_name:
        return jsonify({"error": "Enter the school term."}), 400

    account = (
        StudentFeeAccount.query.filter_by(student_id=student.id)
        .with_for_update()
        .first()
    )
    if not account:
        account = StudentFeeAccount(
            student_id=student.id,
            account_number=student.registration_number.replace("EDU", "FEE"),
            term_id=term.id if term else None,
            total_fee=0,
            total_paid=0,
            current_balance=0,
            status="Unpaid",
        )
        db.session.add(account)
        db.session.flush()

    previous_balance = Decimal(account.current_balance or 0)
    if previous_balance <= 0 and total_fee is not None:
        if total_fee <= 0:
            return jsonify({"error": "Amount due must be greater than 0."}), 400
        account.total_fee = total_fee
        account.current_balance = total_fee
        previous_balance = total_fee
    elif previous_balance <= 0:
        return jsonify({"error": "This student has no fee balance. Enter the amount due before recording payment."}), 400
    if amount > previous_balance:
        return jsonify({"error": f"Payment cannot exceed the current balance of ${previous_balance:.2f}."}), 400

    try:
        payment_date = date.fromisoformat(data.get("paymentDate")) if data.get("paymentDate") else date.today()
    except ValueError:
        return jsonify({"error": "Payment date must be a valid date."}), 400
    recorder_id = int(get_jwt_identity())
    payment = Payment(
        payment_reference=f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}",
        student_id=student.id,
        fee_account_id=account.id,
        term_id=term.id if term else None,
        term_name=term_name,
        amount=amount,
        method=(data.get("paymentMethod") or "Cash").strip(),
        reference_number=(data.get("referenceNumber") or "").strip() or None,
        note=(data.get("note") or "").strip() or None,
        previous_balance=previous_balance,
        new_balance=previous_balance - amount,
        recorded_by_id=recorder_id,
        paid_at=datetime.combine(payment_date, time.min),
    )
    db.session.add(payment)
    db.session.flush()

    account.term_id = term.id if term else None
    account.total_paid = Decimal(account.total_paid or 0) + amount
    account.current_balance = previous_balance - amount
    account.status = account_status(account)

    db.session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": 2026000001})
    receipt = Receipt(
        receipt_number=next_receipt_number(),
        payment_id=payment.id,
        student_id=student.id,
        amount=amount,
        issued_by_id=recorder_id,
    )
    db.session.add(receipt)
    db.session.flush()
    receipt.pdf_url = f"/api/accounts/receipts/{receipt.id}/download"
    write_audit("payment_recorded", "Payment", payment.id, {"registrationNumber": registration, "amount": float(amount)})
    write_audit("receipt_generated", "Receipt", receipt.id, {"receiptNumber": receipt.receipt_number})
    db.session.commit()
    return jsonify({"message": "Payment recorded successfully.", "payment": payment.to_dict(), "receipt": receipt.to_dict(), "account": account.to_dict()}), 201


@accounts_payments_bp.get("/payments")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def list_account_payments():
    query = Payment.query
    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.join(Student).filter(or_(Payment.payment_reference.ilike(like), Student.registration_number.ilike(like), Student.first_name.ilike(like), Student.last_name.ilike(like)))
    return jsonify({"items": [payment_with_receipt(item) for item in query.order_by(Payment.paid_at.desc(), Payment.id.desc()).limit(200).all()]})


@accounts_payments_bp.get("/receipts/<int:receipt_id>")
@jwt_required()
def receipt_detail(receipt_id):
    receipt = db.session.get(Receipt, receipt_id)
    if not receipt or not visible_student(receipt.student_id):
        return jsonify({"error": "Receipt not found."}), 404
    return jsonify({"receipt": receipt.to_dict(), "payment": receipt.payment.to_dict(), "student": student_summary(receipt.student)})


def school_name():
    setting = SchoolSetting.query.filter(SchoolSetting.key.in_(["school_name", "schoolName"])).first()
    return setting.value if setting else "EduTrack School"


@accounts_payments_bp.get("/receipts/<int:receipt_id>/download")
@jwt_required()
def download_receipt(receipt_id):
    receipt = db.session.get(Receipt, receipt_id)
    if not receipt or not visible_student(receipt.student_id):
        return jsonify({"error": "Receipt not found."}), 404
    payment = receipt.payment
    student = receipt.student
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20 * mm, leftMargin=20 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    styles = getSampleStyleSheet()
    rows = [
        ["Receipt number", receipt.receipt_number],
        ["Student registration", student.registration_number],
        ["Student name", student.to_dict()["name"]],
        ["Form / Class", student.school_class.name if student.school_class else student.grade_form or "-"],
        ["Stream", student.class_stream or "-"],
        ["Term", payment.term.name if payment.term else payment.term_name or "-"],
        ["Amount paid", f"${payment.amount:.2f}"],
        ["Previous balance", f"${payment.previous_balance:.2f}"],
        ["New balance", f"${payment.new_balance:.2f}"],
        ["Payment method", payment.method],
        ["Payment date", payment.paid_at.strftime("%d %B %Y")],
        ["Accountant", payment.recorded_by.to_dict()["name"] if payment.recorded_by else "-"],
        ["Reference / note", payment.reference_number or payment.note or "-"],
    ]
    table = Table(rows, colWidths=[55 * mm, 100 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    document.build([Paragraph(school_name(), styles["Title"]), Paragraph("Official Fee Payment Receipt", styles["Heading2"]), Spacer(1, 8 * mm), table, Spacer(1, 8 * mm), Paragraph("Thank you for your payment.", styles["Normal"])])
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True, download_name=f"{receipt.receipt_number}.pdf")


@parent_payments_bp.get("/children/<int:student_id>/payments")
@jwt_required()
def parent_student_payments(student_id):
    student = visible_student(student_id)
    if not student:
        return jsonify({"error": "Student payment information not found."}), 404
    payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.paid_at.desc(), Payment.id.desc()).all()
    return jsonify({"student": student_summary(student), "payments": [payment_with_receipt(item) for item in payments]})


@admin_payments_bp.get("/payments/summary")
@jwt_required()
@roles_required("Admin", "Super Admin")
def admin_payment_summary():
    accounts = StudentFeeAccount.query.join(Student).order_by(Student.grade_form, Student.last_name).all()
    return jsonify({"items": [item.to_dict() for item in accounts]})


@admin_payments_bp.get("/students/<int:student_id>/fees")
@jwt_required()
@roles_required("Admin", "Super Admin")
def admin_student_fees(student_id):
    student = db.session.get(Student, student_id)
    if not student:
        return jsonify({"error": "Student not found."}), 404
    payments = Payment.query.filter_by(student_id=student.id).order_by(Payment.paid_at.desc()).all()
    return jsonify({"student": student_summary(student), "account": student.fee_account.to_dict() if student.fee_account else None, "payments": [payment_with_receipt(item) for item in payments]})
