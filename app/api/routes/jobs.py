import csv
import codecs
import re
from fastapi import APIRouter, Depends, Header, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import GenerationJob
from app.schemas.job import JobCreateRequest, JobCreateResponse, JobStatusResponse
from app.schemas.certificate import PaginatedCertificateResponse, CertificateResponse
from app.core.security import verify_api_key
from app.core.logging import logger
from app.services.job_service import process_job_creation

router = APIRouter(prefix="/api/jobs", tags=["jobs"], dependencies=[Depends(verify_api_key)])

@router.post("", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job_json(
    request: JobCreateRequest,
    idempotency_key: str = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    recipients = [{"name": r.name, "email": r.email} for r in request.recipients]
    
    job = process_job_creation(
        db=db,
        event_name=request.event_name,
        event_date=request.event_date,
        certificate_title=request.certificate_title,
        recipients=recipients,
        idempotency_key=idempotency_key
    )
    
    return JobCreateResponse(job_id=str(job.id), status=job.status.value, total=job.total_count)

@router.post("/csv", response_model=JobCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_job_csv(
    event_name: str = Form(...),
    event_date: str = Form(...),
    certificate_title: str = Form(...),
    file: UploadFile = File(...),
    idempotency_key: str = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    csv_reader = csv.DictReader(codecs.iterdecode(file.file, 'utf-8'))
    
    if not csv_reader.fieldnames or "name" not in csv_reader.fieldnames or "email" not in csv_reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV must contain exact 'name' and 'email' header columns")

    recipients = []
    errors = []
    email_regex = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")

    for row_num, row in enumerate(csv_reader, start=2): # Start at 2 because row 1 is headers
        name = row.get("name", "").strip()
        email = row.get("email", "").strip()
        
        if not name:
            errors.append(f"Row {row_num}: Missing name")
        elif not email or not email_regex.match(email):
            errors.append(f"Row {row_num}: Invalid email '{email}'")
        else:
            recipients.append({"name": name, "email": email})

    if errors:
        raise HTTPException(status_code=400, detail={"message": "Invalid CSV data found", "errors": errors})
        
    if not recipients:
        raise HTTPException(status_code=400, detail="CSV contains no valid data rows")
        
    if len(recipients) > 5000:
        raise HTTPException(status_code=400, detail="Maximum 5000 recipients allowed per batch")

    job = process_job_creation(
        db=db,
        event_name=event_name,
        event_date=event_date,
        certificate_title=certificate_title,
        recipients=recipients,
        idempotency_key=idempotency_key
    )
    
    return JobCreateResponse(job_id=str(job.id), status=job.status.value, total=job.total_count)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    pending = job.total_count - (job.success_count + job.failed_count)
    progress = 0.0
    if job.total_count > 0:
        progress = round(((job.success_count + job.failed_count) / job.total_count) * 100, 2)

    return JobStatusResponse(
        job_id=str(job.id),
        event_name=job.event_name,
        status=job.status.value,
        total=job.total_count,
        successful=job.success_count,
        failed=job.failed_count,
        pending=pending,
        progress_percentage=progress
    )

@router.get("/{job_id}/certificates", response_model=PaginatedCertificateResponse)
def list_job_certificates(
    job_id: str, 
    page: int = 1, 
    page_size: int = 20, 
    db: Session = Depends(get_db)
):
    page = max(1, page)
    page_size = min(100, max(1, page_size))
    offset = (page - 1) * page_size
    
    total_certs = db.query(Certificate).filter(Certificate.job_id == job_id).count()
    certificates = db.query(Certificate).filter(Certificate.job_id == job_id).offset(offset).limit(page_size).all()
        
    return PaginatedCertificateResponse(
        items=[
            CertificateResponse(
                id=str(c.id), job_id=str(c.job_id), recipient_name=c.recipient_name,
                recipient_email=c.recipient_email, status=c.status.value,
                error_message=c.error_message, created_at=c.created_at
            ) for c in certificates
        ],
        page=page, page_size=page_size, total=total_certs
    )