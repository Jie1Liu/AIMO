# AIMO

AIMO, short for AI Marketing Officer, is an AI CMO workspace for finding potential customers, drafting human-reviewed outreach, and turning public market signals into product and marketing recommendations.

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

## Core Safety Rule

AI can discover, analyze, draft, summarize, and recommend. AIMO does not implement mass unsolicited messaging. Every outbound message must be personalized, policy-checked, human-reviewed, approved, rate-limited, and logged. Reddit MVP sends are manual copy/open-original actions only.

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

## Start Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://127.0.0.1:3000`.

## MVP Pages

- `/`
- `/onboarding`
- `/town`
- `/business-brain`
- `/accounts`
- `/leads`
- `/review`
- `/conversations`
- `/analytics`
- `/settings`
