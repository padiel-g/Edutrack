from datetime import date, datetime
from decimal import Decimal

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from sqlalchemy import func, or_

from app.extensions import db, limiter
from app.models import FeeReminder, Invoice, InvoiceItem, Payment, Receipt, SchoolClass, Student, StudentFeeAccount
from app.services.audit import write_audit
from app.services.finance import refresh_invoice_status
from app.services.numbering import next_invoice_number, next_receipt_number
from app.utils.security import roles_required

finance_bp = Blueprint("finance", __name__)


def money(value):
    return Decimal(str(value or 0))


def paginated_response(query, serializer):
    try:
        page = max(int(request.args.get("page", 1)), 1)
        per_page = min(max(int(request.args.get("perPage", 25)), 1), 100)
    except ValueError:
        page, per_page = 1, 25
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    return jsonify(
        {
            "items": [serializer(item) for item in pagination.items],
            "total": pagination.total,
            "page": page,
            "perPage": per_page,
        }
    )


@finance_bp.get("/dashboard")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def dashboard():
    total_invoiced = db.session.query(func.coalesce(func.sum(Invoice.amount), 0)).scalar()
    total_paid = db.session.query(func.coalesce(func.sum(Payment.amount), 0)).scalar()
    today = date.today()
    by_status = {status: Invoice.query.filter_by(status=status).count() for status in ["Paid", "Unpaid", "Partially Paid", "Overdue"]}
    paid_month = func.to_char(Payment.paid_at, "YYYY-MM")
    monthly = (
        db.session.query(paid_month, func.coalesce(func.sum(Payment.amount), 0))
        .group_by(paid_month)
        .order_by(paid_month)
        .all()
    )
    methods = db.session.query(Payment.method, func.coalesce(func.sum(Payment.amount), 0)).group_by(Payment.method).all()
    return jsonify(
        {
            "totals": {
                "totalInvoiced": float(total_invoiced),
                "totalPaid": float(total_paid),
                "outstandingBalance": float(total_invoiced - total_paid),
                "paidStudents": by_status["Paid"],
                "unpaidStudents": by_status["Unpaid"],
                "partiallyPaidStudents": by_status["Partially Paid"],
                "overdueInvoices": by_status["Overdue"],
                "todaysCollections": float(
                    db.session.query(func.coalesce(func.sum(Payment.amount), 0))
                    .filter(func.date(Payment.paid_at) == today)
                    .scalar()
                ),
            },
            "monthlyCollections": [{"month": month or "Current", "amount": float(amount)} for month, amount in monthly],
            "paidVsUnpaid": [{"name": key, "value": value} for key, value in by_status.items()],
            "paymentMethods": [{"name": method, "value": float(amount)} for method, amount in methods],
            "outstandingByClass": outstanding_by_class(),
        }
    )


@finance_bp.get("/fee-accounts")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def fee_accounts():
    query = StudentFeeAccount.query
    status = (request.args.get("status") or "").strip()
    if status:
        query = query.filter(StudentFeeAccount.status == status)
    student_id = request.args.get("studentId")
    if student_id:
        query = query.filter(StudentFeeAccount.student_id == int(student_id))
    return paginated_response(query.order_by(StudentFeeAccount.id.desc()), lambda item: item.to_dict())


@finance_bp.get("/invoices")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def invoices():
    query = Invoice.query
    search = (request.args.get("search") or "").strip()
    if search:
        like = f"%{search}%"
        query = query.join(Student, Invoice.student_id == Student.id).filter(
            or_(Invoice.invoice_number.ilike(like), Student.registration_number.ilike(like), Student.first_name.ilike(like), Student.last_name.ilike(like))
        )
    status = (request.args.get("status") or "").strip()
    if status:
        query = query.filter(Invoice.status == status)
    student_id = request.args.get("studentId")
    if student_id:
        query = query.filter(Invoice.student_id == int(student_id))
    return paginated_response(query.order_by(Invoice.id.desc()), lambda item: item.to_dict())


@finance_bp.post("/invoices")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
@limiter.limit("30 per minute")
def create_invoice():
    data = request.get_json() or {}
    student = db.session.get(Student, data["studentId"])
    if not student:
        return jsonify({"error": "Student not found"}), 404
    account = student.fee_account or StudentFeeAccount(student_id=student.id, account_number=student.registration_number.replace("EDU", "FEE"), current_balance=0)
    db.session.add(account)
    amount = money(data["amount"])
    invoice = Invoice(
        invoice_number=next_invoice_number(),
        student_id=student.id,
        fee_account=account,
        term_id=data.get("termId") or 1,
        academic_year_id=student.academic_year_id,
        amount=amount,
        paid_amount=0,
        balance=amount,
        due_date=date.fromisoformat(data["dueDate"]),
        status="Unpaid",
    )
    db.session.add(invoice)
    db.session.flush()
    db.session.add(
        InvoiceItem(
            invoice_id=invoice.id,
            description=data.get("description", "School fees"),
            quantity=1,
            unit_amount=amount,
            total_amount=amount,
        )
    )
    account.term_id = invoice.term_id
    account.total_fee = money(account.total_fee) + amount
    account.current_balance = money(account.current_balance) + amount
    account.status = "Partially Paid" if money(account.total_paid) > 0 else "Unpaid"
    write_audit("invoice_created", "Invoice", invoice.id, {"invoiceNumber": invoice.invoice_number})
    db.session.commit()
    return jsonify({"item": invoice.to_dict()}), 201


@finance_bp.post("/bulk-invoices")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
@limiter.limit("5 per minute")
def create_bulk_invoices():
    data = request.get_json() or {}
    students = Student.query.filter_by(class_id=data["classId"], status="active").all()
    created = []
    for student in students:
        request_data = {
            "studentId": student.id,
            "amount": data["amount"],
            "dueDate": data["dueDate"],
            "description": data.get("description", "Class fee invoice"),
            "termId": data.get("termId") or 1,
        }
        # Inline creation keeps one transaction for the class batch.
        account = student.fee_account or StudentFeeAccount(student_id=student.id, account_number=student.registration_number.replace("EDU", "FEE"), current_balance=0)
        db.session.add(account)
        amount = money(request_data["amount"])
        invoice = Invoice(invoice_number=next_invoice_number(), student_id=student.id, fee_account=account, term_id=request_data["termId"], academic_year_id=student.academic_year_id, amount=amount, paid_amount=0, balance=amount, due_date=date.fromisoformat(request_data["dueDate"]), status="Unpaid")
        db.session.add(invoice)
        db.session.flush()
        db.session.add(InvoiceItem(invoice_id=invoice.id, description=request_data["description"], quantity=1, unit_amount=amount, total_amount=amount))
        account.term_id = invoice.term_id
        account.total_fee = money(account.total_fee) + amount
        account.current_balance = money(account.current_balance) + amount
        account.status = "Partially Paid" if money(account.total_paid) > 0 else "Unpaid"
        created.append(invoice)
    write_audit("bulk_invoices_created", "Invoice", None, {"classId": data["classId"], "count": len(created)})
    db.session.commit()
    return jsonify({"items": [invoice.to_dict() for invoice in created], "count": len(created)}), 201


@finance_bp.post("/payments")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
@limiter.limit("30 per minute")
def record_payment():
    data = request.get_json() or {}
    invoice = db.session.get(Invoice, data["invoiceId"])
    if not invoice:
        return jsonify({"error": "Invoice not found"}), 404
    payment = Payment(payment_reference=data.get("paymentReference") or f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}", invoice_id=invoice.id, student_id=invoice.student_id, amount=money(data["amount"]), method=data.get("method", "Cash"))
    db.session.add(payment)
    db.session.flush()
    refresh_invoice_status(invoice)
    receipt = Receipt(receipt_number=next_receipt_number(), payment_id=payment.id, student_id=invoice.student_id, amount=payment.amount)
    db.session.add(receipt)
    write_audit("payment_recorded", "Payment", payment.id, {"invoiceNumber": invoice.invoice_number})
    write_audit("receipt_generated", "Receipt", receipt.id, {"receiptNumber": receipt.receipt_number})
    db.session.commit()
    return jsonify({"payment": payment.to_dict(), "receipt": receipt.to_dict(), "invoice": invoice.to_dict()}), 201


@finance_bp.get("/payments")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def payments():
    query = Payment.query
    search = (request.args.get("search") or "").strip()
    if search:
        query = query.filter(Payment.payment_reference.ilike(f"%{search}%"))
    student_id = request.args.get("studentId")
    if student_id:
        query = query.filter(Payment.student_id == int(student_id))
    return paginated_response(query.order_by(Payment.id.desc()), lambda item: item.to_dict())


@finance_bp.get("/receipts")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def receipts():
    query = Receipt.query
    search = (request.args.get("search") or "").strip()
    if search:
        query = query.filter(Receipt.receipt_number.ilike(f"%{search}%"))
    student_id = request.args.get("studentId")
    if student_id:
        query = query.filter(Receipt.student_id == int(student_id))
    return paginated_response(query.order_by(Receipt.id.desc()), lambda item: item.to_dict())


@finance_bp.post("/reminders")
@jwt_required()
@roles_required("Accounts Officer", "Admin", "Super Admin")
def send_reminder():
    data = request.get_json() or {}
    reminder = FeeReminder(student_id=data["studentId"], invoice_id=data.get("invoiceId"), message=data.get("message", "Please settle your outstanding balance."), channel=data.get("channel", "email"), status="Queued")
    db.session.add(reminder)
    write_audit("fee_reminder_created", "FeeReminder", None, {"studentId": data["studentId"]})
    db.session.commit()
    return jsonify({"item": {"id": reminder.id, "status": reminder.status}}), 201


def outstanding_by_class():
    rows = (
        db.session.query(SchoolClass.name, func.coalesce(func.sum(Invoice.balance), 0))
        .join(Student, Student.class_id == SchoolClass.id)
        .join(Invoice, Invoice.student_id == Student.id)
        .group_by(SchoolClass.name)
        .all()
    )
    return [{"className": name, "amount": float(amount)} for name, amount in rows]
