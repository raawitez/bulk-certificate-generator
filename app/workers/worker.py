import json
import pika
import time
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import logger
from app.db.database import SessionLocal
from app.db.models import Certificate, GenerationJob, CertificateStatus, JobStatus
from app.services.generator import CertificateGenerator
from app.services.storage import storage_service

QUEUE_NAME = "certificate_generation"

def update_job_status_if_complete(db: Session, job_id: str):
    job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
    if not job:
        return
    
    processed_count = job.success_count + job.failed_count
    if processed_count >= job.total_count:
        if job.failed_count > 0:
            job.status = JobStatus.COMPLETED_WITH_ERRORS
        else:
            job.status = JobStatus.COMPLETED
        db.commit()
        logger.info(f"Job {job.id} fully completed with status: {job.status.value}")

def process_message(ch, method, properties, body):
    db: Session = SessionLocal()
    cert_id = None
    job_id = None
    try:
        message = json.loads(body)
        job_id = message.get("job_id")
        cert_id = message.get("certificate_id")

        cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        
        if not cert or not job:
            logger.warning(f"Certificate {cert_id} or Job not found. Dropping message.")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if cert.status in [CertificateStatus.SUCCESS, CertificateStatus.FAILED]:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        cert.status = CertificateStatus.PROCESSING
        db.commit()

        logger.info(f"Generating PDF for {cert.recipient_name}...")
        
        pdf_bytes = CertificateGenerator.generate(
            name=cert.recipient_name,
            event_name=job.event_name,
            event_date=job.event_date,
            cert_title=job.certificate_title,
            cert_id=str(cert.id)
        )
        
        filename = f"{cert.id}.pdf"
        file_path = storage_service.save(filename, pdf_bytes)

        cert.file_path = file_path
        cert.status = CertificateStatus.SUCCESS
        
        db.query(GenerationJob).filter(GenerationJob.id == job_id).update(
            {"success_count": GenerationJob.success_count + 1}
        )
        db.commit()
        
        logger.info(f"Successfully processed certificate {cert_id}")

    except Exception as e:
        logger.error(f"Failed to process certificate {cert_id}: {e}", exc_info=True)
        db.rollback()
        
        try:
            if cert_id and job_id:
                cert = db.query(Certificate).filter(Certificate.id == cert_id).first()
                if cert:
                    cert.status = CertificateStatus.FAILED
                    cert.error_message = str(e)
                    db.query(GenerationJob).filter(GenerationJob.id == job_id).update(
                        {"failed_count": GenerationJob.failed_count + 1}
                    )
                    db.commit()
        except Exception as inner_e:
            logger.error(f"Failed to save error state: {inner_e}")
            db.rollback()

    finally:
        if job_id:
            update_job_status_if_complete(db, job_id)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        db.close()

def start_worker():
    logger.info("Starting RabbitMQ Worker...")
    
    connection = None
    while not connection:
        try:
            parameters = pika.URLParameters(settings.RABBITMQ_URL)
            connection = pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            logger.warning("RabbitMQ not ready yet, retrying in 2 seconds...")
            time.sleep(2)

    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    
    channel.basic_qos(prefetch_count=1)
    
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=process_message)

    logger.info("Worker successfully connected to RabbitMQ. Waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    start_worker()