"""
All Supabase table operations.  Each function accepts only plain Python types
and returns plain dicts so callers stay decoupled from the Supabase SDK.
"""
from __future__ import annotations

from typing import Any
from uuid import UUID

from db.client import get_client


# ─── helpers ──────────────────────────────────────────────────────────────────

def _db():
    return get_client()


def _unwrap(response) -> list[dict]:
    """Extract the data list from a Supabase response, raising on error."""
    if hasattr(response, "error") and response.error:
        raise RuntimeError(f"Supabase error: {response.error}")
    return response.data or []


def _one(response) -> dict | None:
    rows = _unwrap(response)
    return rows[0] if rows else None


# ─── tasks ────────────────────────────────────────────────────────────────────

def create_task(
    title: str,
    description: str | None = None,
    due_date: str | None = None,
    priority: str = "medium",
) -> dict:
    payload: dict[str, Any] = {"title": title, "priority": priority}
    if description:
        payload["description"] = description
    if due_date:
        payload["due_date"] = due_date

    resp = _db().table("tasks").insert(payload).execute()
    row = _one(resp)
    if row is None:
        raise RuntimeError("create_task: no row returned")
    return row


def get_all_tasks(status: str | None = None) -> list[dict]:
    q = _db().table("tasks").select("*").order("created_at", desc=True)
    if status:
        q = q.eq("status", status)
    return _unwrap(q.execute())


def get_task(task_id: str | UUID) -> dict | None:
    resp = _db().table("tasks").select("*").eq("id", str(task_id)).execute()
    return _one(resp)


def update_task_status(task_id: str | UUID, status: str) -> dict | None:
    resp = (
        _db()
        .table("tasks")
        .update({"status": status})
        .eq("id", str(task_id))
        .execute()
    )
    return _one(resp)


def update_task(task_id: str | UUID, fields: dict[str, Any]) -> dict | None:
    resp = (
        _db()
        .table("tasks")
        .update(fields)
        .eq("id", str(task_id))
        .execute()
    )
    return _one(resp)


def delete_task(task_id: str | UUID) -> bool:
    resp = _db().table("tasks").delete().eq("id", str(task_id)).execute()
    return len(_unwrap(resp)) > 0


# ─── resumes ──────────────────────────────────────────────────────────────────

def save_resume(raw_text: str) -> dict:
    resp = _db().table("resumes").insert({"raw_text": raw_text}).execute()
    row = _one(resp)
    if row is None:
        raise RuntimeError("save_resume: no row returned")
    return row


def get_latest_resume() -> dict | None:
    resp = (
        _db()
        .table("resumes")
        .select("*")
        .order("uploaded_at", desc=True)
        .limit(1)
        .execute()
    )
    return _one(resp)


def get_resume(resume_id: str | UUID) -> dict | None:
    resp = (
        _db()
        .table("resumes")
        .select("*")
        .eq("id", str(resume_id))
        .execute()
    )
    return _one(resp)


# ─── interview_sessions ───────────────────────────────────────────────────────

def save_session(
    company: str,
    jd_text: str,
    questions: list[str],
    answers: list[str],
    resume_id: str | UUID | None = None,
    insights: str | None = None,
) -> dict:
    payload: dict[str, Any] = {
        "company": company,
        "jd_text": jd_text,
        "questions": questions,
        "answers": answers,
    }
    if resume_id:
        payload["resume_id"] = str(resume_id)
    if insights:
        payload["insights"] = insights

    resp = _db().table("interview_sessions").insert(payload).execute()
    row = _one(resp)
    if row is None:
        raise RuntimeError("save_session: no row returned")
    return row


def get_all_sessions(company: str | None = None) -> list[dict]:
    q = (
        _db()
        .table("interview_sessions")
        .select("*")
        .order("created_at", desc=True)
    )
    if company:
        q = q.eq("company", company)
    return _unwrap(q.execute())


def get_session(session_id: str | UUID) -> dict | None:
    resp = (
        _db()
        .table("interview_sessions")
        .select("*")
        .eq("id", str(session_id))
        .execute()
    )
    return _one(resp)
