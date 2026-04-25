# Architecture — Modular Personal AI Agent Platform

## Overview

A monorepo containing a FastAPI backend (deployed on Render) and a Next.js 14
frontend (deployed on Vercel), backed by Supabase (PostgreSQL) and powered by
Groq's llama3-70b-8192 LLM. Two domain agents — Task Tracker and Interview Prep
— are independently routable and share a common LLM wrapper and DB client.

---

## Folder Structure

```
/                                  ← monorepo root
├── .env.example                   ← all env var keys (no values)
├── .gitignore
├── README.md                      ← setup, run, deploy docs
│
├── backend/                       ← FastAPI application
│   ├── requirements.txt           ← Python dependencies
│   ├── Dockerfile                 ← container config for Render
│   │
│   ├── app/
│   │   ├── main.py                ← FastAPI app factory; mounts routers; CORS config
│   │   ├── config.py              ← Pydantic BaseSettings; loads all env vars
│   │   ├── dependencies.py        ← shared FastAPI Depends() factories
│   │   │
│   │   ├── core/
│   │   │   ├── llm.py             ← Groq client wrapper; single chat_completion() fn
│   │   │   └── scheduler.py       ← APScheduler instance; job registration helpers
│   │   │
│   │   ├── db/
│   │   │   ├── supabase_client.py ← Supabase client singleton (service role key)
│   │   │   └── models.py          ← SQLAlchemy-free table helpers; raw Supabase ops
│   │   │
│   │   ├── schemas/
│   │   │   ├── task.py            ← Pydantic models: TaskCreate, TaskRead, TaskUpdate
│   │   │   └── interview.py       ← Pydantic models: QuestionRequest, QuestionResponse
│   │   │
│   │   ├── agents/
│   │   │   ├── base_agent.py      ← Abstract Agent class: run(), system_prompt property
│   │   │   ├── task_tracker.py    ← TaskTrackerAgent: manages tasks via LLM + Supabase
│   │   │   └── interview_prep.py  ← InterviewPrepAgent: generates Q&A, tracks sessions
│   │   │
│   │   └── api/
│   │       ├── router.py          ← top-level APIRouter; includes tasks + interview sub-routers
│   │       ├── tasks.py           ← /api/tasks CRUD + /api/tasks/chat endpoint
│   │       └── interview.py       ← /api/interview/question, /api/interview/evaluate
│   │
│   └── tests/
│       ├── conftest.py            ← pytest fixtures; TestClient setup
│       ├── test_tasks.py          ← unit + integration tests for task endpoints
│       └── test_interview.py      ← unit + integration tests for interview endpoints
│
├── frontend/                      ← Next.js 14 application
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   │
│   ├── app/                       ← Next.js App Router
│   │   ├── layout.tsx             ← root layout; fonts; global providers
│   │   ├── page.tsx               ← landing / dashboard redirect
│   │   ├── globals.css            ← Tailwind base styles
│   │   │
│   │   ├── tasks/
│   │   │   └── page.tsx           ← Task Tracker UI page
│   │   │
│   │   └── interview/
│   │       └── page.tsx           ← Interview Prep UI page
│   │
│   ├── components/
│   │   ├── ui/
│   │   │   ├── Button.tsx         ← reusable button component
│   │   │   ├── Card.tsx           ← card wrapper
│   │   │   └── Input.tsx          ← text input with label
│   │   ├── TaskList.tsx           ← renders list of tasks from API
│   │   ├── TaskForm.tsx           ← form to create / update tasks via chat
│   │   ├── InterviewChat.tsx      ← Q&A chat interface for interview prep
│   │   └── Navbar.tsx             ← top navigation bar
│   │
│   ├── lib/
│   │   ├── api.ts                 ← typed fetch helpers; base URL from env
│   │   └── types.ts               ← shared TypeScript interfaces matching backend schemas
│   │
│   └── public/                    ← static assets
│
└── tasks/                         ← project management docs
    ├── todo.md
    ├── in_progress.md
    ├── finished.md
    ├── lessons.md
    ├── prompts_log.md
    └── ARCHITECTURE.md            ← this file
```

---

## Data Flow Diagram

```
User (Browser)
     │
     │  HTTP request (fetch / axios)
     ▼
Next.js Frontend (Vercel)
     │  lib/api.ts  →  NEXT_PUBLIC_API_URL
     │
     │  POST /api/tasks/chat  OR  POST /api/interview/question
     ▼
FastAPI Backend (Render)
     │
     ├─ app/main.py             ← CORS + lifespan
     ├─ app/api/router.py       ← route dispatch
     │
     ├── /api/tasks/*  ──────►  agents/task_tracker.py
     │                               │
     │                               ├─► core/llm.py
     │                               │       │
     │                               │       └─► Groq API (llama3-70b-8192)
     │                               │               │
     │                               │           LLM response
     │                               │
     │                               └─► db/supabase_client.py
     │                                       │
     │                                       └─► Supabase (PostgreSQL)
     │                                               │
     │                                           rows read/written
     │
     └── /api/interview/*  ──►  agents/interview_prep.py
                                     │
                                     ├─► core/llm.py  ──►  Groq API
                                     │
                                     └─► db/supabase_client.py  ──►  Supabase
     │
     │  JSON response
     ▼
Next.js Frontend
     │  React state update
     ▼
Rendered UI (user sees result)
```

---

## Supabase Tables

### tasks
| column       | type      | notes                        |
|--------------|-----------|------------------------------|
| id           | uuid (PK) | gen_random_uuid()            |
| user_id      | text      | clerk/auth user id (future)  |
| title        | text      | task title                   |
| description  | text      | optional detail               |
| status       | text      | todo / in_progress / done    |
| due_date     | date      | optional                     |
| created_at   | timestamptz | default now()              |
| updated_at   | timestamptz | default now()              |

### interview_sessions
| column       | type      | notes                        |
|--------------|-----------|------------------------------|
| id           | uuid (PK) | gen_random_uuid()            |
| user_id      | text      |                              |
| topic        | text      | e.g. "Python", "System Design"|
| question     | text      | LLM-generated question       |
| user_answer  | text      | user's submitted answer      |
| evaluation   | text      | LLM feedback on answer       |
| score        | int       | 0-10 rating                  |
| created_at   | timestamptz | default now()              |

---

## Environment Variables

### Backend  (.env in /backend or root)

| Variable                  | Description                                |
|---------------------------|--------------------------------------------|
| GROQ_API_KEY              | Groq API key (console.groq.com)            |
| SUPABASE_URL              | Supabase project URL                       |
| SUPABASE_SERVICE_KEY      | Supabase service role key (server-only)    |
| ALLOWED_ORIGINS           | Comma-separated CORS origins               |
| ENVIRONMENT               | development / production                   |
| PORT                      | Port for uvicorn (default 8000)            |

### Frontend  (.env.local in /frontend)

| Variable                      | Description                            |
|-------------------------------|----------------------------------------|
| NEXT_PUBLIC_API_URL           | Full URL of deployed FastAPI backend   |
| NEXT_PUBLIC_SUPABASE_URL      | Supabase project URL (public)          |
| NEXT_PUBLIC_SUPABASE_ANON_KEY | Supabase anon key (public, read-safe)  |

---

## Agent Responsibilities

### TaskTrackerAgent
- System prompt: productivity-focused task manager
- Actions: create task, list tasks, update status, summarize backlog
- Scheduler: daily digest job via APScheduler (lists overdue tasks)
- LLM: interprets natural language commands into structured task ops

### InterviewPrepAgent
- System prompt: senior technical interviewer
- Actions: generate question by topic, evaluate user answer, score response
- Persistence: saves each Q&A session to interview_sessions table
- LLM: generates contextually appropriate questions and detailed feedback
