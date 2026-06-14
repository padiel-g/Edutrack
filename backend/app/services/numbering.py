from datetime import date

from app.models import Invoice, Receipt, Student


def next_sequence(model, field_name, prefix, year=None, width=4):
    year = year or date.today().year
    stem = f"{prefix}-{year}-"
    latest = model.query.filter(getattr(model, field_name).like(f"{stem}%")).order_by(getattr(model, field_name).desc()).first()
    if not latest:
        number = 1
    else:
        number = int(getattr(latest, field_name).split("-")[-1]) + 1
    return f"{stem}{number:0{width}d}"


def next_registration_number():
    return next_sequence(Student, "registration_number", "EDU")


def next_invoice_number():
    return next_sequence(Invoice, "invoice_number", "INV")


def next_receipt_number():
    return next_sequence(Receipt, "receipt_number", "REC", width=6)
