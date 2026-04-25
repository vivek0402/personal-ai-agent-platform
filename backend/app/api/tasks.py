import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agents.task_agent import parse_and_save_task
from app.api.responses import ok, err
from app.schemas.task import TaskInput
from db.queries import get_all_tasks, update_task_status, delete_task

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tasks"])


class StatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|in_progress|done)$")


@router.post("", status_code=201)
def create_task(body: TaskInput):
    """Parse natural-language input and save a new task."""
    try:
        result = parse_and_save_task(body.user_input)
        return ok(result.model_dump())
    except ValueError as exc:
        logger.warning("create_task bad input: %s", exc)
        return JSONResponse(status_code=422, content=err(str(exc)))
    except Exception as exc:
        logger.error("create_task error: %s", exc)
        return JSONResponse(status_code=500, content=err("Failed to create task"))


@router.get("")
def list_tasks(status: str | None = None):
    """Return all tasks, optionally filtered by status."""
    try:
        tasks = get_all_tasks(status=status)
        return ok(tasks)
    except Exception as exc:
        logger.error("list_tasks error: %s", exc)
        return JSONResponse(status_code=500, content=err("Failed to fetch tasks"))


@router.patch("/{task_id}")
def patch_task_status(task_id: str, body: StatusUpdate):
    """Update a task's status field."""
    try:
        updated = update_task_status(task_id, body.status)
        if updated is None:
            return JSONResponse(
                status_code=404,
                content=err(f"Task '{task_id}' not found"),
            )
        return ok(updated)
    except Exception as exc:
        logger.error("patch_task error: %s", exc)
        return JSONResponse(status_code=500, content=err("Failed to update task"))


@router.delete("/{task_id}")
def remove_task(task_id: str):
    """Permanently delete a task."""
    try:
        deleted = delete_task(task_id)
        if not deleted:
            return JSONResponse(
                status_code=404,
                content=err(f"Task '{task_id}' not found"),
            )
        return ok({"deleted": True, "id": task_id})
    except Exception as exc:
        logger.error("delete_task error: %s", exc)
        return JSONResponse(status_code=500, content=err("Failed to delete task"))
