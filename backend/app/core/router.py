"""
Intent router — classifies free-text user input into one of three buckets:
  "task"       → forward to TaskTrackerAgent
  "interview"  → forward to InterviewPrepAgent
  "unknown"    → return a helpful fallback message
"""
import json
import logging

from app.core.llm import call_llm
from app.schemas.router import RouterDecision

logger = logging.getLogger(__name__)

_VALID_INTENTS = ("task", "interview", "unknown")

_SYSTEM_PROMPT = """
You are an intent classifier for a personal AI assistant.
Classify the user's message into exactly one category:
  - "task"      : user wants to create, view, update, or delete tasks / reminders / to-dos
  - "interview" : user wants interview prep help, practice questions, resume review, or career coaching
  - "unknown"   : anything else

Few-shot examples:

User: add a task to review my pull request
{"intent": "task", "confidence": 0.97}

User: remind me to send the quarterly report by Friday
{"intent": "task", "confidence": 0.95}

User: what are all my pending tasks?
{"intent": "task", "confidence": 0.93}

User: help me prepare for my Amazon software engineer interview
{"intent": "interview", "confidence": 0.96}

User: give me five Python coding questions for interview practice
{"intent": "interview", "confidence": 0.95}

User: how should I answer behavioural questions about leadership?
{"intent": "interview", "confidence": 0.92}

User: what is the weather like today?
{"intent": "unknown", "confidence": 0.98}

User: tell me a joke about programmers
{"intent": "unknown", "confidence": 0.97}

User: who won the last FIFA World Cup?
{"intent": "unknown", "confidence": 0.95}

Return ONLY a raw JSON object with keys "intent" and "confidence". No prose, no markdown fences.
""".strip()


def route_intent(user_input: str) -> RouterDecision:
    """
    Classify *user_input* and return a RouterDecision.

    Falls back to intent="unknown" / confidence=0.0 on any LLM or parse error
    so the caller always receives a valid RouterDecision.
    """
    try:
        raw = call_llm(_SYSTEM_PROMPT, user_input)
        # Strip accidental markdown fences the model might add
        cleaned = (
            raw.strip()
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        data = json.loads(cleaned)
        intent = str(data.get("intent", "unknown"))
        if intent not in _VALID_INTENTS:
            logger.warning("Unexpected intent value %r — falling back to unknown.", intent)
            intent = "unknown"
        confidence = max(0.0, min(1.0, float(data.get("confidence", 0.5))))

    except Exception as exc:
        logger.warning("Intent routing failed, defaulting to unknown: %s", exc)
        intent = "unknown"
        confidence = 0.0

    return RouterDecision(intent=intent, confidence=confidence, raw_input=user_input)  # type: ignore[arg-type]
