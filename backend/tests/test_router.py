"""
Router tests — 6 cases (2 per intent category).

call_llm is patched so no real Groq API key or network call is required.
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest


# ─── helpers ──────────────────────────────────────────────────────────────────

def _llm_json(intent: str, confidence: float) -> str:
    return json.dumps({"intent": intent, "confidence": confidence})


# ─── task intent ──────────────────────────────────────────────────────────────

class TestTaskIntent:
    def test_create_task_message(self):
        with patch("app.core.router.call_llm", return_value=_llm_json("task", 0.97)):
            from app.core.router import route_intent

            result = route_intent("add a task to review my pull request")

        assert result.intent == "task"
        assert result.confidence == pytest.approx(0.97)
        assert "pull request" in result.raw_input

    def test_list_tasks_message(self):
        with patch("app.core.router.call_llm", return_value=_llm_json("task", 0.93)):
            from app.core.router import route_intent

            result = route_intent("show me all my pending tasks")

        assert result.intent == "task"
        assert result.confidence >= 0.9
        assert result.raw_input == "show me all my pending tasks"


# ─── interview intent ─────────────────────────────────────────────────────────

class TestInterviewIntent:
    def test_interview_prep_message(self):
        with patch("app.core.router.call_llm", return_value=_llm_json("interview", 0.96)):
            from app.core.router import route_intent

            result = route_intent("help me prepare for my Amazon interview")

        assert result.intent == "interview"
        assert result.confidence >= 0.9

    def test_practice_questions_message(self):
        with patch("app.core.router.call_llm", return_value=_llm_json("interview", 0.95)):
            from app.core.router import route_intent

            result = route_intent("give me python coding questions")

        assert result.intent == "interview"
        assert result.raw_input == "give me python coding questions"


# ─── unknown intent ───────────────────────────────────────────────────────────

class TestUnknownIntent:
    def test_weather_message(self):
        with patch("app.core.router.call_llm", return_value=_llm_json("unknown", 0.98)):
            from app.core.router import route_intent

            result = route_intent("what is the weather today?")

        assert result.intent == "unknown"
        assert result.confidence == pytest.approx(0.98)

    def test_invalid_llm_response_falls_back_to_unknown(self):
        with patch("app.core.router.call_llm", return_value="not valid json {{{}"):
            from app.core.router import route_intent

            result = route_intent("some random message")

        assert result.intent == "unknown"
        assert result.confidence == pytest.approx(0.0)
