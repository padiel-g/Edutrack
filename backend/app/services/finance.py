from datetime import date
from decimal import Decimal


def refresh_invoice_status(invoice):
    paid = sum((payment.amount for payment in invoice.payments), Decimal("0"))
    invoice.paid_amount = paid
    invoice.balance = Decimal(invoice.amount or 0) - paid
    if invoice.balance <= 0:
        invoice.status = "Paid"
        invoice.balance = Decimal("0")
    elif paid > 0:
        invoice.status = "Partially Paid"
    elif invoice.due_date and invoice.due_date < date.today():
        invoice.status = "Overdue"
    else:
        invoice.status = "Unpaid"

    if invoice.fee_account:
        invoice.fee_account.current_balance = invoice.balance
