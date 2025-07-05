import pika
import json
from src.en_service.en_analyzer import analyze_text

def main():
    FEEDBACK_QUEUE = "analyzer-feedback-queue"
    WORKER_QUEUE = "analyzer-job-queue"

    connection, job_channel, notify_channel = initialize_channel(FEEDBACK_QUEUE,WORKER_QUEUE)
    start_consumer(job_channel,notify_channel, WORKER_QUEUE, FEEDBACK_QUEUE)

def initialize_channel(notifier_queue, receiver_queue):
    RABBITMQ_HOST = "localhost"
    RABBITMQ_PORT = 30000
    RABBITMQ_USER = "rabbitMQ"
    RABBITMQ_PASSWORD = "rabbitMQ"
    connection_parameters = pika.ConnectionParameters(
        host=RABBITMQ_HOST,
        port=RABBITMQ_PORT,
        credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
)
    connection = pika.BlockingConnection(connection_parameters)
    
    job_channel = connection.channel()
    notify_channel = connection.channel()

    job_channel.queue_declare(queue=receiver_queue, durable=True)
    notify_channel.queue_declare(queue=notifier_queue, durable=True)

    return connection, job_channel, notify_channel


def start_consumer(job_channel, notify_channel, receiver_queue, notifier_queue):
    def process_message(ch, method, properties, body):
        payload = json.loads(body.decode())
        text = payload["text"]
        job_id = payload["job_id"]
        requester_id = payload["requester_id"]
        print(f"Received job {job_id} from {requester_id}")
        print(f"Text: {text}")

        analyzed_text = analyze_text(text)
        print(f"Analyzed text: {analyzed_text}")

        response = json.dumps({"requester_id": requester_id, "job_id": job_id, "original_text": text, "analysis": analyzed_text})
        publish_notification(notify_channel, notifier_queue, response)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    job_channel.basic_qos(prefetch_count=1)
    job_channel.basic_consume(queue=receiver_queue, auto_ack=False, on_message_callback=process_message)
    job_channel.start_consuming()

def publish_notification(channel, queue_name, message):
    channel.basic_publish(exchange='', routing_key=queue_name, body=message)

if __name__ == "__main__":
    main()