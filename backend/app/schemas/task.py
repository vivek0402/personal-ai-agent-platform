from typing import Optional

from pydantic import BaseModel, Field


class TaskInput(BaseModel):
    user_input: str = Field(..., min_length=1, max_length=1000)


class TaskResponse(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    due_date: Optional[str] = None
    priority: str
    status: str
    created_at: str
    confirmation_message: str


class ReminderPayload(BaseModel):
    task_id: str
    title: str
    due_date: Optional[str] = None
    message: str = ""
