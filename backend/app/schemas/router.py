from typing import Literal

from pydantic import BaseModel, Field


class RouterDecision(BaseModel):
    intent: Literal["task", "interview", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    raw_input: str
