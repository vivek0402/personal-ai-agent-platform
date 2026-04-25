# Lessons & Decisions

## Architecture Decisions

### Why 3 separate LLM calls in the interview agent (not one big prompt)
Each step (company insights, question generation, SAR answers) has a different
"mode of thinking" for the LLM. A single 3000-token prompt produces generic
output because the model's attention is distributed. Three focused prompts —
each with a clear single objective and few-shot examples — produce noticeably
higher quality. The latency cost (~3x API roundtrips) is acceptable for a
one-time prep kit generation.

### Why Supabase over raw SQLite
SQLite is fine for a local prototype but breaks the moment you deploy to
Render (ephemeral filesystem — data is wiped on each deploy). Supabase gives
you a free hosted Postgres instance, a REST API, and a web dashboard for free,
with a clean Python SDK. Upgrade path to pgvector for semantic search is a
single extension enable.

### Why APScheduler inside FastAPI (not a separate Celery/RQ worker)
For an MVP with one developer, running APScheduler in the FastAPI process
eliminates the need for Redis, a separate worker process, and a message broker.
The trade-off: if the server restarts, scheduled jobs are lost and must be
re-hydrated from the DB on startup — which the scheduler already does. For
production scale, swap to Celery + Redis without changing the agent/query layer.

## Trade-offs Accepted for MVP

### No authentication
Single-user assumed. All tasks and sessions are globally readable. Adding
Supabase Auth (JWT-based) is the first upgrade — it only requires adding
a `user_id` column to each table and a `Depends(get_current_user)` on each
route.

### No vector database yet
Resumes and JDs are stored as raw text. Semantic search (e.g., "find me
sessions where I discussed FAISS") is not yet possible. The upgrade path is
clear: enable the `pgvector` extension in Supabase, add an `embedding` column
to `interview_sessions`, and call an embedding model on ingest.

### Reminders are server-side HTTP POSTs only
The scheduler fires an internal HTTP POST to `/api/webhooks/reminder` and
stamps `reminded_at` on the task. There is no email, SMS, or push notification.
This is intentional for the MVP — it keeps the backend dependency-free. Adding
Resend (email) or Expo push tokens is a thin layer on top of the existing
webhook endpoint.

## Design Patterns That Worked Well

### Offline test suite (conftest.py stubs)
Stubbing `supabase`, `groq`, `apscheduler`, and `pydantic_settings` in
conftest.py at the `sys.modules` level means the entire backend test suite
runs in 0.4s with no API keys, no network, and no running services. This
pattern should be replicated in any future agent added to the platform.

### { success, data, error } response envelope
Returning a consistent envelope from every route — regardless of whether the
operation succeeded — means the frontend never needs to check HTTP status codes
before reading the body. Error handling in the UI is a single `if (!resp.success)`
branch. HTTP status codes are still set correctly (201, 404, 422, 500) for
interoperability with external clients.

### Graceful LLM fallbacks
The intent router falls back to `"unknown"` on any LLM or JSON parse error.
The interview agent's question/answer parsers fall back to line-splitting if
JSON.parse fails. These fallbacks mean a badly-formatted LLM response degrades
gracefully rather than crashing the user's request.

## Windows-Specific Lessons

### cp1252 terminal encoding
Windows terminals default to cp1252, which cannot encode Unicode box-drawing
characters (U+2500), em-dashes (U+2014), or arrows (U+2192). All print
statements in test files must use ASCII equivalents (`-`, `--`, `->`) to
avoid UnicodeEncodeError during pytest -s runs.

## Next Upgrades

- **Supabase Auth** — multi-user support with JWT; add `user_id` to all tables
- **pgvector / FAISS** — semantic search over resumes and past sessions
- **Email/push reminders** — wire Resend (email) or Expo push to the existing
  `/api/webhooks/reminder` endpoint
- **More agents** — cold email writer, LinkedIn post optimizer, mock interview
  voice mode (Whisper + TTS)
- **Celery + Redis** — replace APScheduler for reliable distributed scheduling
  under production load
