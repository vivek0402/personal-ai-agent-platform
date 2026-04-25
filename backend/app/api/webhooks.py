"""Internal webhook endpoints — fired by APScheduler reminders."""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter

from app.api.responses import ok, err
from app.schemas.task import ReminderPayload
from db.queries import update_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])


@router.post("/reminder")
def receive_reminder(payload: ReminderPayload):
    """
    Called by the scheduler when a task reminder fires.
    Logs the event and stamps reminded_at on the task row.
    """
    try:
        logger.info(
            "Reminder received — task_id=%s title='%s' due=%s",
            payload.task_id, payload.title, payload.due_date,
        )
        update_task(
            payload.task_id,
            {"reminded_at": datetime.now(timezone.utc).isoformat()},
        )
        return ok({"received": True, "task_id": payload.task_id, "title": payload.title})
    except Exception as exc:
        logger.error("Reminder webhook error: %s", exc)
        return err(str(exc))
