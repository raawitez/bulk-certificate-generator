import io
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors

class CertificateGenerator:
    @staticmethod
    def generate(name: str, event_name: str, event_date: str, cert_title: str, cert_id: str) -> bytes:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)

        c.setStrokeColor(colors.HexColor("#2C3E50"))
        c.setLineWidth(5)
        c.rect(0.5 * inch, 0.5 * inch, width - 1 * inch, height - 1 * inch)
        
        c.setLineWidth(1)
        c.rect(0.6 * inch, 0.6 * inch, width - 1.2 * inch, height - 1.2 * inch)

        c.setFont("Helvetica-Bold", 36)
        c.setFillColor(colors.HexColor("#2C3E50"))
        c.drawCentredString(width / 2.0, height - 2 * inch, cert_title)

        c.setFont("Helvetica", 18)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2.0, height - 3 * inch, "This is proudly presented to")

        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(colors.HexColor("#E74C3C"))
        c.drawCentredString(width / 2.0, height - 4 * inch, name)

        c.setFont("Helvetica", 16)
        c.setFillColor(colors.black)
        c.drawCentredString(width / 2.0, height - 5 * inch, f"For successfully completing: {event_name}")
        c.drawCentredString(width / 2.0, height - 5.5 * inch, f"Date: {event_date}")

        c.setFont("Helvetica-Oblique", 10)
        c.setFillColor(colors.gray)
        c.drawCentredString(width / 2.0, 1 * inch, f"Certificate ID: {cert_id}")

        c.showPage()
        c.save()

        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes