from pydantic import BaseModel, Field


class InterviewRequest(BaseModel):
    company: str = Field(..., min_length=1, max_length=200)
    jd_text: str = Field(..., min_length=50, max_length=10_000)
    resume_text: str = Field(..., min_length=50, max_length=10_000)


class InterviewPrepResult(BaseModel):
    session_id: str
    company: str
    insights: str
    questions: list[str]       # exactly 10: 4 behavioral, 4 technical, 2 situational
    answers: list[str]         # SAR answer for each question, same order
