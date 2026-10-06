import json
import pika
from app.core.config import settings
from app.core.logging import logger

QUEUE_NAME = "certificate_generation"

def get_rabbitmq_connection():
    parameters = pika.URLParameters(settings.RABBITMQ_URL)
    return pika.BlockingConnection(parameters)

def publish_certificate_tasks(job_id: str, certificate_ids: list[str]):
    try:
        connection = get_rabbitmq_connection()
        channel = connection.channel()
        
        channel.queue_declare(queue=QUEUE_NAME, durable=True)
        
        for cert_id in certificate_ids:
            message = {
                "job_id": job_id,
                "certificate_id": cert_id
            }
            
            channel.basic_publish(
                exchange='',
                routing_key=QUEUE_NAME,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )
            )
            
        connection.close()
        logger.info(f"Successfully published {len(certificate_ids)} tasks for job {job_id} to RabbitMQ")
        
    except Exception as e:
        logger.error(f"Failed to publish messages to RabbitMQ for job {job_id}: {e}", exc_info=True)