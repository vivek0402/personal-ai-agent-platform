# AI Agent Platform

A production-grade personal AI assistant with two intelligent agents — a
**Task Manager** that parses natural-language descriptions into structured tasks
with adaptive reminders, and an **Interview Prep** coach that runs a 3-step LLM
pipeline to generate company insights, 10 JD-grounded questions, and
personalised SAR answers from your real resume. Built with FastAPI, Supabase,
Groq llama3-70b-8192, and Next.js 14.

---

## Repository Layout

```
/
├── backend/                  FastAPI application (Python 3.11)
│   ├── app/
│   │   ├── agents/           task_agent.py, interview_agent.py
│   │   ├── api/              tasks, interview, webhooks, health routes
│   │   ├── core/             llm.py (Groq + 3-retry backoff), router.py
│   │   ├── db/               supabase_client.py, queries.py, migrations/
│   │   ├── schemas/          Pydantic models
│   │   └── tools/            scheduler.py (APScheduler reminders)
│   ├── tests/                58 tests — fully offline
│   ├── render.yaml           Render Blueprint IaC
│   └── requirements.txt
│
├── frontend/                 Next.js 14 (TypeScript + Tailwind CSS)
│   ├── app/
│   │   ├── page.tsx          Landing with two CTA cards
│   │   ├── tasks/page.tsx    Task Manager UI
│   │   ├── interview/page.tsx Interview Prep UI
│   │   ├── error.tsx         Route-level error boundary
│   │   └── global-error.tsx  App-level error boundary
│   ├── components/           Navbar, reusable UI
│   ├── lib/                  api.ts (all fetches), types.ts
│   └── vercel.json           Vercel config
│
└── tasks/                    Project docs + architecture decisions
```

---

## Features

| Agent | Capability |
|---|---|
| Task Manager | NL input → LLM extracts title + due date + priority → Supabase |
| Task Manager | APScheduler fires reminders: 24h before (>2 days out) or 6h before (≤2 days) |
| Interview Prep | Step A: company culture + interview style analysis |
| Interview Prep | Step B: 10 questions — 4 behavioral, 4 technical (from JD), 2 situational |
| Interview Prep | Step C: SAR answers that cite your actual resume projects and metrics |

---

## Example Usage

### Task Manager

```
Input:  "Apply to Zepto by this Friday, high priority"
Output: Task saved: 'Apply to Zepto' — due 2026-04-25 — [high priority].
        Reminder scheduled: fires 24h before due date.
```

### Interview Prep

```
Input:  company="Zepto", paste full JD, paste resume
Output: 
  Company Insights — culture, interview style, red flags to avoid
  Q1 (Behavioral): "Tell me about a time you owned an ML project end-to-end..."
  A1: "S: Building FinTrack, I was the sole engineer with 4 weeks...
       A: I prioritised the LLM-powered categorisation core first...
       R: 500 active users, 8,000 transactions/month."
  ... (10 Q&A pairs total, persisted to Supabase)
```

---

## API Reference

All responses: `{ "success": bool, "data": any, "error": string | null }`

| Method | Path | Status | Description |
|---|---|---|---|
| GET | `/health` | 200 | Health check |
| POST | `/api/tasks` | 201 | Create task from natural language |
| GET | `/api/tasks` | 200 | List tasks (`?status=pending`) |
| PATCH | `/api/tasks/{id}` | 200 / 404 | Update task status |
| DELETE | `/api/tasks/{id}` | 200 / 404 | Delete task |
| POST | `/api/webhooks/reminder` | 200 | Internal — reminder received |
| POST | `/api/interview/prep` | 201 | 3-step prep pipeline |
| POST | `/api/interview/resume` | 201 | Save resume |
| GET | `/api/interview/sessions` | 200 | List sessions |

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Supabase](https://supabase.com) project (free tier)
- [Groq](https://console.groq.com) API key (free tier)

### 1 — Configure environment

```bash
git clone <your-repo-url> && cd <repo>
cp .env.example .env
# Fill in GROQ_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

### 2 — Run Supabase migration

Open Supabase → **SQL Editor** → paste and run `backend/db/migrations/001_init.sql`

Creates three tables: `tasks`, `resumes`, `interview_sessions`

### 3 — Start backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Swagger docs: `http://localhost:8000/docs`

### 4 — Start frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev                         # http://localhost:3000
```

### 5 — Run tests

```bash
cd backend
pytest tests/ -v
# 58 passed in ~0.4s — no API keys or network needed
```

---

## Deployment

### Supabase (one-time)

1. Create project → **SQL Editor** → run `backend/db/migrations/001_init.sql`
2. Copy **Project URL** → `SUPABASE_URL`
3. Copy **service_role** key → `SUPABASE_KEY`

### Backend → Render

**Blueprint (recommended):** Render → New → Blueprint → connect repo →
Render detects `backend/render.yaml` → set 4 env vars:

| Var | Value |
|---|---|
| `GROQ_API_KEY` | From console.groq.com |
| `SUPABASE_URL` | From Supabase Settings > API |
| `SUPABASE_KEY` | service_role secret |
| `FRONTEND_URL` | Set after Vercel deploy |

**Manual:** Root Dir = `backend`, Build = `pip install -r requirements.txt`,
Start = `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Frontend → Vercel

Vercel → New Project → import repo → Root Dir = `frontend` →
add env var `NEXT_PUBLIC_API_URL` = your Render URL → Deploy

### Wire together

After both deploy: set `FRONTEND_URL` in Render = your Vercel URL.
This enables CORS from the production frontend domain.

### Verify

```bash
curl https://your-backend.onrender.com/health
# {"status":"ok","version":"1.0.0"}
```

---

## Environment Variables

### Backend

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | Yes | Groq API key |
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase service-role key (server only) |
| `FRONTEND_URL` | Prod | Vercel URL — added to CORS allowlist |
| `ALLOWED_ORIGINS` | No | Extra CORS origins (default: localhost:3000) |
| `ENVIRONMENT` | No | `development` or `production` |

### Frontend

| Variable | Required | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | Yes | FastAPI backend URL |

---

## Architecture Notes

- **LLM provider:** Groq free tier — llama3-70b-8192 — 3 retries with exponential backoff
- **3 separate LLM calls** in the interview agent keep each step focused; one monolithic prompt produces generic output
- **APScheduler** runs inside the FastAPI process — no extra infra for MVP; swap to Celery for production scale
- **Offline test suite** — all 58 tests mock Supabase and Groq; runs in 0.4s with no credentials
- **Error envelope** — every response is `{ success, data, error }` so frontend error handling is a single `if (!resp.success)` branch
