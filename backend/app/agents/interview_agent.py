"""
Interview Prep Agent — 3-step LLM pipeline.

Step A  Company Insights  : Analyse company + JD → culture, interview style, values, red flags
Step B  Question Generation: Generate exactly 10 grounded questions (4 behav / 4 tech / 2 sit)
Step C  Personalised Answers: SAR-format answers citing the candidate's real resume artefacts

Every LLM call is separate so each prompt is focused and the model's context
stays on one job at a time — mixing all three steps into one prompt produces
generic, lower-quality output.
"""
from __future__ import annotations

import json
import logging

from app.core.llm import call_llm
from app.schemas.interview import InterviewPrepResult
from db.queries import save_session

logger = logging.getLogger(__name__)


# ─── Step A — Company Insights ────────────────────────────────────────────────

_INSIGHTS_PROMPT = """
You are a senior interview coach with deep knowledge of tech companies and startup culture.

Analyse the company and job description below. Return a structured plaintext report covering:

1. Company Culture & Values — what this organisation actually rewards
2. Interview Style — technical depth, behavioural emphasis, case studies, take-homes
3. What This Team Values in Candidates — the top 3-4 traits that differentiate offers
4. Red Flags to Avoid — specific answer patterns, attitudes, or gaps that lose offers here

Be specific to THIS company and THIS JD. No generic advice.

Company: {company}
Job Description:
{jd}
""".strip()


def _step_a_insights(company: str, jd: str) -> str:
    prompt = _INSIGHTS_PROMPT.format(company=company, jd=jd)
    return call_llm(prompt, "Generate the company insights report.")


# ─── Step B — Question Generation ─────────────────────────────────────────────

_QUESTIONS_PROMPT = """
You are a senior interviewer at {company} hiring for the role described below.

Generate exactly 10 interview questions in this order:
  Q1-Q4  : Behavioral — leadership, failure, teamwork, growth mindset
  Q5-Q8  : Technical  — grounded in the specific technologies and responsibilities in the JD
  Q9-Q10 : Situational — realistic on-the-job scenarios this role will face in the first 6 months

Rules:
- EVERY question must reference content from the JD. No generic questions.
- Technical questions must name specific tools, systems, or scale from the JD.
- Return ONLY a raw JSON array of 10 strings. No numbering, no prose, no fences.

Job Description:
{jd}

Company Insights (use for context):
{insights}
""".strip()


def _step_b_questions(company: str, jd: str, insights: str) -> list[str]:
    prompt = _QUESTIONS_PROMPT.format(company=company, jd=jd, insights=insights)
    raw = call_llm(prompt, "Generate the 10 interview questions.")
    cleaned = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
        questions: list[str] = json.loads(cleaned)
        if not isinstance(questions, list):
            raise ValueError("Expected a JSON array")
        return [str(q).strip() for q in questions[:10]]
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Step B JSON parse failed: %s\nRaw: %s", exc, raw)
        # Fallback: split on newlines and return whatever we got
        lines = [ln.strip(" -•\t") for ln in raw.splitlines() if ln.strip()]
        return lines[:10] if lines else [raw]


# ─── Step C — Personalised SAR Answers ───────────────────────────────────────

_ANSWERS_PROMPT = """
You are coaching a candidate preparing for a {company} interview.

Candidate Resume:
{resume}

Rules — MANDATORY, no exceptions:
- NO GENERIC ANSWERS. Every answer MUST cite a specific project, metric, or skill from the resume above.
- Use SAR format: Situation (1 sentence) → Action (2 sentences) → Result (1 sentence with a metric).
- Each answer must be 4 sentences maximum.
- If the resume does not contain direct experience for a question, adapt the closest project and state the transferable skill explicitly.

Return ONLY a raw JSON array of {n} strings — one answer per question, same order.
No numbering, no labels, no markdown fences.

Questions:
{questions_json}
""".strip()


def _step_c_answers(questions: list[str], resume: str, company: str) -> list[str]:
    prompt = _ANSWERS_PROMPT.format(
        company=company,
        resume=resume,
        n=len(questions),
        questions_json=json.dumps(questions, indent=2),
    )
    raw = call_llm(prompt, "Generate the personalised SAR answers.")
    cleaned = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )
    try:
        answers: list[str] = json.loads(cleaned)
        if not isinstance(answers, list):
            raise ValueError("Expected a JSON array")
        return [str(a).strip() for a in answers[: len(questions)]]
    except (json.JSONDecodeError, ValueError) as exc:
        logger.error("Step C JSON parse failed: %s\nRaw: %s", exc, raw)
        lines = [ln.strip(" -•\t") for ln in raw.splitlines() if ln.strip()]
        return lines[: len(questions)] if lines else [raw]


# ─── Public entry point ───────────────────────────────────────────────────────

def run_interview_prep(jd: str, resume: str, company: str) -> InterviewPrepResult:
    """
    Run the full 3-step interview prep pipeline and persist the session.

    Args:
        jd:      Full job description text.
        resume:  Candidate's resume as plain text.
        company: Company name (used in prompts and DB).

    Returns:
        InterviewPrepResult with insights, 10 questions, and 10 SAR answers.
    """
    logger.info("Interview prep started — company=%s", company)

    insights = _step_a_insights(company, jd)
    logger.info("Step A complete — insights length=%d", len(insights))

    questions = _step_b_questions(company, jd, insights)
    logger.info("Step B complete — %d questions generated", len(questions))

    answers = _step_c_answers(questions, resume, company)
    logger.info("Step C complete — %d answers generated", len(answers))

    session = save_session(
        company=company,
        jd_text=jd,
        questions=questions,
        answers=answers,
        insights=insights,
    )
    logger.info("Session saved — id=%s", session.get("id"))

    return InterviewPrepResult(
        session_id=str(session["id"]),
        company=company,
        insights=insights,
        questions=questions,
        answers=answers,
    )
