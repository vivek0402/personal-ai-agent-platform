"""
Task agent tests — 3 realistic natural language inputs.

Mocks:
  - app.agents.task_agent.call_llm   → controlled JSON string
  - app.agents.task_agent.create_task → fake Supabase row (no network)

Each test verifies:
  - Correct field extraction from NL input
  - Correct priority and due_date mapping
  - Confirmation message content
  - Saved status is "pending"
"""
from __future__ import annotations

import json
from unittest.mock import patch

import pytest


# ─── helpers ──────────────────────────────────────────────────────────────────

def _llm_json(title: str, description, due_date, priority: str) -> str:
    return json.dumps({
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
    })


def _saved_row(
    title: str,
    due_date,
    priority: str,
    description=None,
    task_id: str = "uuid-test-1",
) -> dict:
    return {
        "id": task_id,
        "title": title,
        "description": description,
        "due_date": due_date,
        "priority": priority,
        "status": "pending",
        "created_at": "2026-04-24T00:00:00Z",
    }


# ─── test 1: Zepto application, high priority, specific Friday ────────────────

class TestApplyToZepto:
    def test_parses_title_priority_and_due_date(self):
        llm_out = _llm_json("Apply to Zepto", None, "2026-04-25", "high")
        saved = _saved_row("Apply to Zepto", "2026-04-25", "high", task_id="uuid-zepto-1")

        with (
            patch("app.agents.task_agent.call_llm", return_value=llm_out),
            patch("app.agents.task_agent.create_task", return_value=saved),
        ):
            from app.agents.task_agent import parse_and_save_task
            result = parse_and_save_task(
                "Remind me to apply to Zepto by this Friday, high priority"
            )

        assert result.title == "Apply to Zepto"
        assert result.priority == "high"
        assert result.due_date == "2026-04-25"
        assert result.status == "pending"
        assert result.id == "uuid-zepto-1"
        assert "Apply to Zepto" in result.confirmation_message
        assert "high" in result.confirmation_message.lower()

    def test_confirmation_includes_due_date(self):
        llm_out = _llm_json("Apply to Zepto", None, "2026-04-25", "high")
        saved = _saved_row("Apply to Zepto", "2026-04-25", "high")

        with (
            patch("app.agents.task_agent.call_llm", return_value=llm_out),
            patch("app.agents.task_agent.create_task", return_value=saved),
        ):
            from app.agents.task_agent import parse_and_save_task
            result = parse_and_save_task("Apply to Zepto by this Friday, high priority")

        assert "2026-04-25" in result.confirmation_message


# ─── test 2: System design practice, tomorrow, default priority ───────────────

class TestSystemDesignTomorrow:
    def test_parses_title_and_medium_priority(self):
        llm_out = _llm_json("Practice system design", "Morning session", "2026-04-25", "medium")
        saved = _saved_row(
            "Practice system design", "2026-04-25", "medium",
            description="Morning session", task_id="uuid-sd-1",
        )

        with (
            patch("app.agents.task_agent.call_llm", return_value=llm_out),
            patch("app.agents.task_agent.create_task", return_value=saved),
        ):
            from app.agents.task_agent import parse_and_save_task
            result = parse_and_save_task("Practice system design tomorrow morning")

        assert result.title == "Practice system design"
        assert result.priority == "medium"
        assert result.due_date == "2026-04-25"
        assert result.description == "Morning session"
        assert result.status == "pending"

    def test_confirmation_mentions_task_name(self):
        llm_out = _llm_json("Practice system design", None, "2026-04-25", "medium")
        saved = _saved_row("Practice system design", "2026-04-25", "medium")

        with (
            patch("app.agents.task_agent.call_llm", return_value=llm_out),
            patch("app.agents.task_agent.create_task", return_value=saved),
        ):
            from app.agents.task_agent import parse_and_save_task
            result = parse_and_save_task("Practice system design tomorrow morning")

        assert "system design" in result.confirmation_message.lower()


# ─── test 3: Read LangChain docs, low priority, next week ─────────────────────

class TestReadLangchainDocs:
    def test_parses_low_priority_and_future_due_date(self):
        llm_out = _llm_json("Read LangChain docs", None, "2026-05-01", "low")
        saved = _saved_row("Read LangChain docs", "2026-05-01", "low", task_id="uuid-lc-1")

        with (
            patch("app.agents.task_agent.call_llm", return_value=llm_out),
            patch("app.agents.task_agent.create_task", return_value=saved),
        ):
            from app.agents.task_agent import parse_and_save_task
            result = parse_and_save_task(
                "Low priority: read LangChain docs sometime next week"
            )

        assert result.title == "Read LangChain docs"
        assert result.priority == "low"
        assert result.due_date == "2026-05-01"
        assert result.status == "pending"
        assert result.id == "uuid-lc-1"

    def test_confirmation_shows_low_priority(self):
        llm_out = _llm_json("Read LangChain docs", None, "2026-05-01", "low")
        saved = _saved_row("Read LangChain docs", "2026-05-01", "low")

        with (
            patch("app.agents.task_agent.call_llm", return_value=llm_out),
            patch("app.agents.task_agent.create_task", return_value=saved),
        ):
            from app.agents.task_agent import parse_and_save_task
            result = parse_and_save_task(
                "Low priority: read LangChain docs sometime next week"
            )

        assert "low" in result.confirmation_message.lower()
        assert "LangChain" in result.confirmation_message


# ─── error handling ───────────────────────────────────────────────────────────

class TestInvalidLLMResponse:
    def test_bad_json_raises_value_error(self):
        with (
            patch("app.agents.task_agent.call_llm", return_value="not valid json {{"),
            patch("app.agents.task_agent.create_task"),
        ):
            from app.agents.task_agent import parse_and_save_task
            with pytest.raises(ValueError, match="unparseable"):
                parse_and_save_task("some task input")

    def test_unknown_priority_defaults_to_medium(self):
        llm_out = _llm_json("Mystery task", None, None, "urgent")  # invalid priority
        saved = _saved_row("Mystery task", None, "medium")

        with (
            patch("app.agents.task_agent.call_llm", return_value=llm_out),
            patch("app.agents.task_agent.create_task", return_value=saved),
        ):
            from app.agents.task_agent import parse_and_save_task
            result = parse_and_save_task("Do something urgent")

        assert result.priority == "medium"
