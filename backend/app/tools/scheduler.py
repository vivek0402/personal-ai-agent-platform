"""
APScheduler-backed reminder scheduler.

Reminder timing rules:
  due > 2 days away  → remind 24 h before due
  due ≤ 2 days away  → remind 6 h before due
  overdue            → fire immediately (5 s delay so startup completes)

On startup, all pending tasks are loaded from Supabase and their reminders
are scheduled.  New tasks are scheduled individually via schedule_task().

Reminders fire an internal HTTP POST to /api/webhooks/reminder so the main
app can handle notification logic in one place.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

from app.config import get_settings
from db.queries import get_all_tasks

logger = logging.getLogger(__name__)

_scheduler: Optional[BackgroundScheduler] = None


# ─── internal helpers ─────────────────────────────────────────────────────────

def _fire_reminder(task_id: str, title: str, due_date: Optional[str]) -> None:
    """POST a reminder event to the internal webhook endpoint."""
    settings = get_settings()
    url = f"http://localhost:{settings.port}/api/webhooks/reminder"
    payload = {"task_id": task_id, "title": title, "due_date": due_date, "message": f"Reminder: '{title}'"}
    try:
        httpx.post(url, json=payload, timeout=5.0)
        logger.info("Reminder fired for task %s ('%s')", task_id, title)
    except Exception as exc:
        logger.warning("Reminder POST failed for task %s: %s", task_id, exc)


def _compute_fire_time(due_date_str: str) -> Optional[datetime]:
    """
    Return the datetime at which the reminder should fire, or None if
    the due_date string cannot be parsed.
    """
    try:
        due = datetime.fromisoformat(due_date_str)
        # If the string is date-only (no time), assume end-of-day
        if due.hour == 0 and due.minute == 0 and due.second == 0:
            due = due.replace(hour=9, minute=0)  # morning of due day
    except (ValueError, TypeError):
        logger.warning("Cannot parse due_date %r — skipping reminder.", due_date_str)
        return None

    now = datetime.now()
    delta = due - now

    if delta.total_seconds() < 0:
        # Already overdue — fire after a short delay so startup finishes first
        return now + timedelta(seconds=5)
    elif delta.days > 2:
        return due - timedelta(hours=24)
    else:
        return due - timedelta(hours=6)


# ─── public API ───────────────────────────────────────────────────────────────

def schedule_task(task: dict) -> None:
    """Add or replace a reminder job for a single task dict."""
    if _scheduler is None or not _scheduler.running:
        logger.debug("Scheduler not running — skipping schedule_task.")
        return

    task_id: str = str(task.get("id", ""))
    title: str = str(task.get("title", "Task"))
    due_date: Optional[str] = task.get("due_date")

    if not due_date:
        return

    fire_at = _compute_fire_time(due_date)
    if fire_at is None:
        return

    job_id = f"reminder_{task_id}"
    _scheduler.add_job(
        _fire_reminder,
        trigger=DateTrigger(run_date=fire_at),
        id=job_id,
        args=[task_id, title, due_date],
        replace_existing=True,
    )
    logger.info(
        "Scheduled reminder: task=%s title='%s' fires_at=%s",
        task_id, title, fire_at.isoformat(),
    )


def start_scheduler() -> None:
    """Start the background scheduler and hydrate reminders from Supabase."""
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.start()
    logger.info("APScheduler started.")

    try:
        pending = get_all_tasks(status="pending")
        for task in pending:
            schedule_task(task)
        logger.info("Loaded %d pending task reminders.", len(pending))
    except Exception as exc:
        logger.warning("Could not hydrate reminders on startup: %s", exc)


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("APScheduler stopped.")
