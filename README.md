# AIMO

AIMO is a Bluesky-first audience intelligence workspace. A founder defines a product,
AIMO searches live public conversations, ranks potential users, drafts contextual replies,
and places the five strongest opportunities into a human review queue.

## Project Structure

```text
aimo/
├── frontend/     # Next.js + TypeScript + Tailwind frontend
├── backend/      # FastAPI + Aurora PostgreSQL-ready backend
├── docs/
├── scripts/
├── infra/
├── docker-compose.yml
├── .env.example
└── README.md
```

## Demo Flow

1. Define the product and target audience.
2. Click **Find users** to search live Bluesky posts.
3. Review, edit, regenerate, or skip each AI-prepared reply.
4. Click **Approve & send** to publish one reviewed reply.

AI can discover, analyze, draft, summarize, and recommend. AIMO does not implement mass
unsolicited messaging. Every outbound message is personalized, policy-checked,
human-reviewed, rate-limited to five per day, and logged.

## Start Infrastructure

```bash
cp .env.example .env
docker compose up -d postgres
```

## Start Backend

```bash
cd backend
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.seed.demo
uvicorn app.main:app --reload
```

The API will run at `http://127.0.0.1:8000`.

For the competition demo, `DATABASE_URL` may be omitted. The backend then creates a
self-contained SQLite database in `/tmp`. PostgreSQL remains supported through
`DATABASE_URL` and Alembic for persistent production deployments.

Configure live Bluesky sending with a dedicated App Password:

```bash
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

Configure any OpenAI-compatible model endpoint:

```bash
LLM_API_STYLE=chat_completions
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=...
LLM_MODEL=gpt-5.5
```

If no model key is configured, the review flow uses a safe contextual template.

## Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://127.0.0.1:3000`.

## MVP Page

- `/` — product brief, live discovery, review queue, and approved sending
