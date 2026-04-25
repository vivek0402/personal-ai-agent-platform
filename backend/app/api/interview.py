import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.agents.interview_agent import run_interview_prep
from app.api.responses import ok, err
from app.schemas.interview import InterviewRequest
from db.queries import save_resume, get_all_sessions

logger = logging.getLogger(__name__)
router = APIRouter(tags=["interview"])


class ResumeInput(BaseModel):
    raw_text: str = Field(..., min_length=10, max_length=20_000)


@router.post("/prep", status_code=201)
def interview_prep(body: InterviewRequest):
    """Run the full 3-step interview prep pipeline and return the result."""
    try:
        result = run_interview_prep(
            jd=body.jd_text,
            resume=body.resume_text,
            company=body.company,
        )
        return ok(result.model_dump())
    except Exception as exc:
        logger.error("interview_prep error: %s", exc)
        return JSONResponse(status_code=500, content=err("Interview prep generation failed"))


@router.post("/resume", status_code=201)
def upload_resume(body: ResumeInput):
    """Persist a resume for use in future interview sessions."""
    try:
        saved = save_resume(body.raw_text)
        return ok(saved)
    except Exception as exc:
        logger.error("upload_resume error: %s", exc)
        return JSONResponse(status_code=500, content=err("Failed to save resume"))


@router.get("/sessions")
def list_sessions(company: str | None = None):
    """Return all interview sessions, optionally filtered by company."""
    try:
        sessions = get_all_sessions(company=company)
        return ok(sessions)
    except Exception as exc:
        logger.error("list_sessions error: %s", exc)
        return JSONResponse(status_code=500, content=err("Failed to fetch sessions"))
