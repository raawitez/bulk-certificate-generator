import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Certificate, CertificateStatus
from app.schemas.certificate import CertificateResponse
from app.core.security import verify_api_key

router = APIRouter(prefix="/api/certificates", tags=["certificates"], dependencies=[Depends(verify_api_key)])

@router.get("/{cert_id}", response_model=CertificateResponse)
def get_certificate(cert_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    return CertificateResponse(
        id=str(cert.id),
        job_id=str(cert.job_id),
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        status=cert.status.value,
        error_message=cert.error_message,
        created_at=cert.created_at
    )

@router.get("/{cert_id}/download")
def download_certificate(cert_id: str, db: Session = Depends(get_db)):
    cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
        
    if cert.status != CertificateStatus.SUCCESS or not cert.file_path:
        raise HTTPException(status_code=400, detail="Certificate is not ready or failed to generate")
        
    if not os.path.exists(cert.file_path):
        raise HTTPException(status_code=404, detail="File missing from storage layer")
        
    return FileResponse(
        path=cert.file_path, 
        filename=f"certificate_{cert.recipient_name.replace(' ', '_')}.pdf",
        media_type="application/pdf"
    )