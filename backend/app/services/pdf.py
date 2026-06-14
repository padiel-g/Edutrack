from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def simple_pdf(title, rows):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 72
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, y, title)
    pdf.setFont("Helvetica", 10)
    y -= 36
    for label, value in rows:
        pdf.drawString(72, y, f"{label}: {value}")
        y -= 18
        if y < 72:
            pdf.showPage()
            y = height - 72
    pdf.save()
    buffer.seek(0)
    return buffer
