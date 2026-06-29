# AIMO Backend

FastAPI backend for AIMO: an AI CMO platform that discovers public market signals, scores lead opportunities, drafts human-reviewed outreach, and generates product recommendations.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.0
- Alembic
- PostgreSQL / Amazon Aurora PostgreSQL
- pgvector extension for optional embeddings
- Amazon SQS, Secrets Manager, and Bedrock-ready configuration

## Local Run

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d postgres
alembic upgrade head
python -m app.seed.demo
uvicorn app.main:app --reload
```

The API runs at `http://127.0.0.1:8000`.

## Docker Run

```bash
cd backend
docker compose up --build
```

## Core Demo Flow

1. `POST /api/products`
2. `POST /api/products/{product_id}/generate-search-strategies`
3. `POST /api/products/{product_id}/run-search`
4. `GET /api/products/{product_id}/leads`
5. `POST /api/leads/{lead_id}/outreach-message`
6. `PATCH /api/outreach-messages/{message_id}` to edit `final_text` or choose an account
7. `POST /api/outreach-messages/{message_id}/approve`
8. `POST /api/outreach-messages/{message_id}/send`
9. `POST /api/products/{product_id}/generate-insights`

Bluesky is the live MVP platform. Public discovery uses the Bluesky AppView search API.
Approved replies are published through AT Protocol only after a human edits and approves
the message. A dedicated Bluesky App Password must be configured on the backend.

## Aurora PostgreSQL Configuration

Set `DATABASE_URL` to your Aurora PostgreSQL connection string:

```bash
DATABASE_URL=postgresql+psycopg://user:password@cluster-endpoint:5432/aimo
```

Run migrations after the database is reachable:

```bash
alembic upgrade head
```

The initial migration enables:

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;
```

Platform credentials and API keys should stay in AWS Secrets Manager or deployment environment variables, never in the repository.
