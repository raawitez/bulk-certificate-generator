from sqlalchemy.orm import Session
from app.db.models import GenerationJob, Certificate, JobStatus
from app.messaging.rabbitmq import publish_certificate_tasks
from app.core.logging import logger

def process_job_creation(
    db: Session, 
    event_name: str, 
    event_date: str, 
    certificate_title: str, 
    recipients: list[dict], 
    idempotency_key: str = None
) -> GenerationJob:
    
    if idempotency_key:
        existing_job = db.query(GenerationJob).filter(GenerationJob.idempotency_key == idempotency_key).first()
        if existing_job:
            logger.info(f"Idempotency hit: Returning existing job {existing_job.id}")
            return existing_job

    new_job = GenerationJob(
        event_name=event_name,
        event_date=event_date,
        certificate_title=certificate_title,
        total_count=len(recipients),
        idempotency_key=idempotency_key,
        status=JobStatus.PENDING
    )
    db.add(new_job)
    db.flush() 

    certificates = [
        Certificate(
            job_id=new_job.id,
            recipient_name=rec["name"],
            recipient_email=rec["email"]
        )
        for rec in recipients
    ]
    db.add_all(certificates)
    db.commit()
    
    cert_ids = [str(cert.id) for cert in certificates]
    publish_certificate_tasks(str(new_job.id), cert_ids)

    logger.info(f"Created new job {new_job.id} with {len(certificates)} recipients")
    return new_job