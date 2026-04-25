"""
FastAPI endpoint tests — all 9 routes.

TestClient drives the full ASGI app; every external call (agent, DB, scheduler)
is mocked so no API keys or network are needed.

Run with:  pytest tests/test_api.py -v -s
"""
from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

# conftest.py has already stubbed supabase / groq / pydantic_settings
from app.main import app


# ─── shared fixture ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """
    TestClient with scheduler lifecycle no-opped.
    We patch the names as they appear in app.main's namespace.
    """
    with (
        patch("app.main.start_scheduler"),
        patch("app.main.stop_scheduler"),
    ):
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


# ─── GET /health ──────────────────────────────────────────────────────────────

class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["version"] == "1.0.0"
        print(f"\n[GET /health] {resp.status_code} ->{body}")


# ─── POST /api/tasks ──────────────────────────────────────────────────────────

_FAKE_TASK_RESPONSE = {
    "id": "uuid-t1", "title": "Apply to Zepto", "description": None,
    "due_date": "2026-04-25", "priority": "high", "status": "pending",
    "created_at": "2026-04-24T00:00:00Z",
    "confirmation_message": "Task saved: 'Apply to Zepto' -- due 2026-04-25 -- [high priority].",
}

class TestCreateTaskEndpoint:
    def test_success_shape(self, client):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = _FAKE_TASK_RESPONSE

        with patch("app.api.tasks.parse_and_save_task", return_value=mock_result):
            resp = client.post(
                "/api/tasks",
                json={"user_input": "Remind me to apply to Zepto by this Friday, high priority"},
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["error"] is None
        assert body["data"]["title"] == "Apply to Zepto"
        assert body["data"]["priority"] == "high"
        print(f"\n[POST /api/tasks] {resp.status_code} ->{json.dumps(body, indent=2)}")

    def test_agent_error_returns_error_shape(self, client):
        with patch("app.api.tasks.parse_and_save_task", side_effect=ValueError("LLM failed")):
            resp = client.post("/api/tasks", json={"user_input": "some task"})

        assert resp.status_code == 422
        body = resp.json()
        assert body["success"] is False
        assert body["error"] is not None
        print(f"\n[POST /api/tasks ERROR] {resp.status_code} ->{body}")


# ─── GET /api/tasks ───────────────────────────────────────────────────────────

_FAKE_TASKS_LIST = [
    {"id": "uuid-t1", "title": "Apply to Zepto", "status": "pending", "priority": "high"},
    {"id": "uuid-t2", "title": "Read LangChain docs", "status": "done", "priority": "low"},
]

class TestListTasksEndpoint:
    def test_returns_list(self, client):
        with patch("app.api.tasks.get_all_tasks", return_value=_FAKE_TASKS_LIST):
            resp = client.get("/api/tasks")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        assert body["data"][0]["title"] == "Apply to Zepto"
        print(f"\n[GET /api/tasks] {resp.status_code} ->{json.dumps(body, indent=2)}")

    def test_status_filter_forwarded(self, client):
        with patch("app.api.tasks.get_all_tasks", return_value=[_FAKE_TASKS_LIST[0]]) as mock_fn:
            resp = client.get("/api/tasks?status=pending")

        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 1
        print(f"\n[GET /api/tasks?status=pending] {resp.status_code} ->{body['data']}")


# ─── PATCH /api/tasks/{id} ────────────────────────────────────────────────────

class TestUpdateTaskEndpoint:
    def test_success(self, client):
        updated_row = {**_FAKE_TASKS_LIST[0], "status": "done"}
        with patch("app.api.tasks.update_task_status", return_value=updated_row):
            resp = client.patch("/api/tasks/uuid-t1", json={"status": "done"})

        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "done"
        print(f"\n[PATCH /api/tasks/uuid-t1] {resp.status_code} ->{json.dumps(body, indent=2)}")

    def test_not_found_returns_error(self, client):
        with patch("app.api.tasks.update_task_status", return_value=None):
            resp = client.patch("/api/tasks/no-such-id", json={"status": "done"})

        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert "not found" in body["error"]
        print(f"\n[PATCH /api/tasks/no-such-id NOT FOUND] {resp.status_code} ->{body}")

    def test_invalid_status_rejected(self, client):
        resp = client.patch("/api/tasks/uuid-t1", json={"status": "invalid_status"})
        # pydantic validation rejects this before hitting our code
        assert resp.status_code == 422
        print(f"\n[PATCH /api/tasks invalid status] {resp.status_code} ->validation error")


# ─── DELETE /api/tasks/{id} ───────────────────────────────────────────────────

class TestDeleteTaskEndpoint:
    def test_success(self, client):
        with patch("app.api.tasks.delete_task", return_value=True):
            resp = client.delete("/api/tasks/uuid-t1")

        body = resp.json()
        assert body["success"] is True
        assert body["data"]["deleted"] is True
        assert body["data"]["id"] == "uuid-t1"
        print(f"\n[DELETE /api/tasks/uuid-t1] {resp.status_code} ->{json.dumps(body, indent=2)}")

    def test_not_found_returns_error(self, client):
        with patch("app.api.tasks.delete_task", return_value=False):
            resp = client.delete("/api/tasks/ghost")

        assert resp.status_code == 404
        body = resp.json()
        assert body["success"] is False
        assert "not found" in body["error"]
        print(f"\n[DELETE /api/tasks/ghost NOT FOUND] {resp.status_code} ->{body}")


# ─── POST /api/webhooks/reminder ─────────────────────────────────────────────

class TestReminderWebhookEndpoint:
    def test_marks_reminded_at(self, client):
        with patch("app.api.webhooks.update_task", return_value={"id": "uuid-t1"}):
            resp = client.post(
                "/api/webhooks/reminder",
                json={
                    "task_id": "uuid-t1",
                    "title": "Apply to Zepto",
                    "due_date": "2026-04-25",
                    "message": "Reminder: task due tomorrow",
                },
            )

        body = resp.json()
        assert body["success"] is True
        assert body["data"]["received"] is True
        assert body["data"]["task_id"] == "uuid-t1"
        print(f"\n[POST /api/webhooks/reminder] {resp.status_code} ->{json.dumps(body, indent=2)}")


# ─── POST /api/interview/prep ─────────────────────────────────────────────────

_FAKE_PREP_RESULT = {
    "session_id": "sess-001",
    "company": "Zepto",
    "insights": "Zepto values speed and ownership.",
    "questions": [f"Question {i}" for i in range(1, 11)],
    "answers":   [f"SAR answer {i}" for i in range(1, 11)],
}

class TestInterviewPrepEndpoint:
    def test_success(self, client):
        mock_result = MagicMock()
        mock_result.model_dump.return_value = _FAKE_PREP_RESULT

        with patch("app.api.interview.run_interview_prep", return_value=mock_result):
            resp = client.post(
                "/api/interview/prep",
                json={
                    "company": "Zepto",
                    "jd_text": "ML Engineer role requiring FAISS and RAG experience. " * 5,
                    "resume_text": "BITS Pilani ME student, built RAG system, FinTrack, Jarvis. " * 5,
                },
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["company"] == "Zepto"
        assert len(body["data"]["questions"]) == 10
        assert len(body["data"]["answers"]) == 10
        print(f"\n[POST /api/interview/prep] {resp.status_code} ->session_id={body['data']['session_id']}, questions={len(body['data']['questions'])}")


# ─── POST /api/interview/resume ───────────────────────────────────────────────

class TestResumeUploadEndpoint:
    def test_success(self, client):
        saved_row = {"id": "res-001", "raw_text": "BITS Pilani resume...", "uploaded_at": "2026-04-24T00:00:00Z"}

        with patch("app.api.interview.save_resume", return_value=saved_row):
            resp = client.post(
                "/api/interview/resume",
                json={"raw_text": "BITS Pilani ME student with RAG system experience."},
            )

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["id"] == "res-001"
        print(f"\n[POST /api/interview/resume] {resp.status_code} ->{json.dumps(body, indent=2)}")


# ─── GET /api/interview/sessions ──────────────────────────────────────────────

_FAKE_SESSIONS = [
    {"id": "sess-001", "company": "Zepto", "created_at": "2026-04-24T00:00:00Z"},
    {"id": "sess-002", "company": "Meesho", "created_at": "2026-04-23T00:00:00Z"},
]

class TestListSessionsEndpoint:
    def test_returns_all_sessions(self, client):
        with patch("app.api.interview.get_all_sessions", return_value=_FAKE_SESSIONS):
            resp = client.get("/api/interview/sessions")

        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        print(f"\n[GET /api/interview/sessions] {resp.status_code} ->{json.dumps(body, indent=2)}")

    def test_company_filter(self, client):
        with patch("app.api.interview.get_all_sessions", return_value=[_FAKE_SESSIONS[0]]):
            resp = client.get("/api/interview/sessions?company=Zepto")

        body = resp.json()
        assert body["success"] is True
        assert body["data"][0]["company"] == "Zepto"
        print(f"\n[GET /api/interview/sessions?company=Zepto] {resp.status_code} ->{body['data']}")
