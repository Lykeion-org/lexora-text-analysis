# lexora-text-analysis

spaCy worker for Lexora. It reads jobs from RabbitMQ, sorts the words of a text into objects (nouns),
actions (verbs) and modifiers (adjectives, adverbs) with their lemma and grammatical attributes, and
publishes the result back. lexora-controller turns every word that is not in the dictionary yet into a
word suggestion. Only English (`en_core_web_sm`) is supported for now.

## Queues

| Queue | Direction | Body |
|---|---|---|
| `analyzer-job-queue` | controller → worker | `{"job_id", "requester_id", "language", "text"}` |
| `analyzer-feedback-queue` | worker → controller | `{"job_id", "requester_id", "language", "original_text", "analysis": {"objects", "actions", "modifiers"}}` |

Each analysed word is `{"text", "lemma", "pos", "attributes"}`. Attribute numbers follow the enums in
`proto/shared/language-types.proto`.

## Running

The worker is part of the local stack in `kosmos/deploy/docker-compose.yml`. To run it on its own:

```bash
make install   # pip install -r requirements.txt (includes the spaCy model)
make run-dev   # python src/main.py
make test
```

Settings come from environment variables:

| Variable | Default |
|---|---|
| `RABBITMQ_URL` | `amqp://rabbitMQ:rabbitMQ@localhost:30000/` (the compose RabbitMQ from the host) |
| `ANALYZER_JOB_QUEUE` | `analyzer-job-queue` |
| `ANALYZER_FEEDBACK_QUEUE` | `analyzer-feedback-queue` |
