import json
import logging
import os
import time

import pika

from en_service.en_analyzer import analyze_text

# Defaults match kosmos/deploy/docker-compose.yml as seen from the host.
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://rabbitMQ:rabbitMQ@localhost:30000/")
JOB_QUEUE = os.getenv("ANALYZER_JOB_QUEUE", "analyzer-job-queue")
FEEDBACK_QUEUE = os.getenv("ANALYZER_FEEDBACK_QUEUE", "analyzer-feedback-queue")

log = logging.getLogger("lexora-text-analysis")


def connect(retries: int = 30, delay: float = 2.0) -> pika.BlockingConnection:
    params = pika.URLParameters(RABBITMQ_URL)
    for attempt in range(1, retries + 1):
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError as err:
            log.warning("RabbitMQ not reachable (attempt %d/%d): %s", attempt, retries, err)
            time.sleep(delay)
    raise SystemExit("could not connect to RabbitMQ")


def process_job(body: bytes) -> dict:
    payload = json.loads(body.decode())
    return {
        "requester_id": payload.get("requester_id", ""),
        "job_id": payload["job_id"],
        "language": payload.get("language", "en"),
        "original_text": payload["text"],
        "analysis": analyze_text(payload["text"]),
    }


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("pika").setLevel(logging.WARNING)
    connection = connect()
    channel = connection.channel()
    channel.queue_declare(queue=JOB_QUEUE, durable=True)
    channel.queue_declare(queue=FEEDBACK_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)

    def on_message(ch, method, properties, body):
        try:
            response = process_job(body)
        except Exception:
            # A malformed job would otherwise be redelivered forever.
            log.exception("Dropping job that could not be analysed")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        analysis = response["analysis"]
        log.info("Analysed job %s: %d objects, %d actions, %d modifiers", response["job_id"],
                 len(analysis["objects"]), len(analysis["actions"]), len(analysis["modifiers"]))
        ch.basic_publish(
            exchange="",
            routing_key=FEEDBACK_QUEUE,
            body=json.dumps(response),
            properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=JOB_QUEUE, on_message_callback=on_message, auto_ack=False)
    log.info("Waiting for jobs on %s", JOB_QUEUE)
    channel.start_consuming()


if __name__ == "__main__":
    main()
