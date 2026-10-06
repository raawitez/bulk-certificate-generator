from app.services.generator import CertificateGenerator

def test_pdf_generation_bytes():
    pdf_bytes = CertificateGenerator.generate(
        name="Test User",
        event_name="Test Event",
        event_date="2026-01-01",
        cert_title="Certificate of Testing",
        cert_id="12345"
    )
    
    assert pdf_bytes is not None
    assert len(pdf_bytes) > 0
    
    assert pdf_bytes.startswith(b"%PDF")