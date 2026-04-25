"""
Task Tracker Agent

Accepts free-text user input, uses the LLM to extract structured task fields,
persists the task to Supabase, and returns a human-readable confirmation.
"""
import json
import logging
from datetime import date

from app.core.llm import call_llm
from app.schemas.task import TaskResponse
from db.queries import create_task

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT_TEMPLATE = """
You are a task extraction assistant. Given free-text about a task or reminder,
extract the fields below and return ONLY a raw JSON object — no prose, no fences.

{{
  "title":       "brief task title (max 60 chars)",
  "description": "optional extra detail, or null",
  "due_date":    "ISO 8601 date YYYY-MM-DD, or null if not mentioned",
  "priority":    "low | medium | high"
}}

Rules:
- Today is {today}. Resolve relative dates ("tomorrow", "this Friday", "next week") to absolute YYYY-MM-DD.
- If no priority is stated, default to "medium".
- If no due date is mentioned, return null for due_date.
- Keep the title concise and action-oriented.
""".strip()


def parse_and_save_task(user_input: str) -> TaskResponse:
    """
    Parse a natural-language task description, persist it, and return a TaskResponse.

    Raises:
        ValueError: If the LLM response cannot be parsed as valid JSON.
    """
    today = date.today().isoformat()
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(today=today)

    raw = call_llm(system_prompt, user_input)

    cleaned = (
        raw.strip()
        .removeprefix("```json")
        .removeprefix("```")
        .removesuffix("```")
        .strip()
    )

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("LLM returned unparseable JSON.\nRaw: %s", raw)
        raise ValueError(f"LLM returned unparseable response: {raw!r}") from exc

    title = str(data.get("title") or "Untitled task").strip()[:60]
    description = data.get("description") or None
    due_date = data.get("due_date") or None
    priority = str(data.get("priority") or "medium").lower()
    if priority not in ("low", "medium", "high"):
        priority = "medium"

    saved = create_task(
        title=title,
        description=description,
        due_date=due_date,
        priority=priority,
    )

    parts = [f"Task saved: '{saved['title']}'"]
    if saved.get("due_date"):
        parts.append(f"due {saved['due_date']}")
    parts.append(f"[{saved.get('priority', priority)} priority]")
    confirmation = " — ".join(parts) + "."

    return TaskResponse(
        id=saved["id"],
        title=saved["title"],
        description=saved.get("description"),
        due_date=saved.get("due_date"),
        priority=saved.get("priority", priority),
        status=saved.get("status", "pending"),
        created_at=str(saved.get("created_at", "")),
        confirmation_message=confirmation,
    )
