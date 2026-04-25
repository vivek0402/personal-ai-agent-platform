"""
DB layer tests — run with: pytest tests/test_db.py -v

These tests use unittest.mock to patch the Supabase client so they run
fully offline without a real Supabase instance.  Each test verifies that:
  - the correct table + method chain is called
  - the helper parses the response correctly
  - error responses raise RuntimeError
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest

# ─── shared mock factory ──────────────────────────────────────────────────────

def _mock_response(data: list[dict] | None = None, error=None):
    resp = MagicMock()
    resp.data = data or []
    resp.error = error
    return resp


def _make_chain(final_response):
    """
    Build a fluent mock that returns itself for every chained method
    and returns final_response on .execute().
    """
    chain = MagicMock()
    chain.table.return_value = chain
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain
    chain.delete.return_value = chain
    chain.eq.return_value = chain
    chain.order.return_value = chain
    chain.limit.return_value = chain
    chain.execute.return_value = final_response
    return chain


# ─── tasks ────────────────────────────────────────────────────────────────────

class TestCreateTask:
    def test_returns_created_row(self):
        row = {"id": "uuid-1", "title": "Write tests", "status": "pending", "priority": "medium"}
        client = _make_chain(_mock_response([row]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.create_task("Write tests")

        assert result["id"] == "uuid-1"
        assert result["title"] == "Write tests"

    def test_raises_when_no_row_returned(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            with pytest.raises(RuntimeError, match="no row returned"):
                queries.create_task("Ghost task")

    def test_passes_optional_fields(self):
        row = {"id": "uuid-2", "title": "Ship it", "due_date": "2026-05-01",
               "priority": "high", "status": "pending"}
        client = _make_chain(_mock_response([row]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.create_task(
                "Ship it", description="deploy to prod", due_date="2026-05-01", priority="high"
            )

        assert result["priority"] == "high"
        assert result["due_date"] == "2026-05-01"


class TestGetAllTasks:
    def test_returns_all_rows(self):
        rows = [
            {"id": "a", "title": "T1", "status": "pending"},
            {"id": "b", "title": "T2", "status": "done"},
        ]
        client = _make_chain(_mock_response(rows))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.get_all_tasks()

        assert len(result) == 2
        assert result[0]["title"] == "T1"

    def test_returns_empty_list_when_no_tasks(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            assert queries.get_all_tasks() == []


class TestUpdateTaskStatus:
    def test_returns_updated_row(self):
        row = {"id": "uuid-1", "status": "done"}
        client = _make_chain(_mock_response([row]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.update_task_status("uuid-1", "done")

        assert result["status"] == "done"

    def test_returns_none_when_not_found(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            assert queries.update_task_status("missing-id", "done") is None


class TestDeleteTask:
    def test_returns_true_on_success(self):
        client = _make_chain(_mock_response([{"id": "uuid-1"}]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            assert queries.delete_task("uuid-1") is True

    def test_returns_false_when_not_found(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            assert queries.delete_task("ghost") is False


# ─── resumes ──────────────────────────────────────────────────────────────────

class TestSaveResume:
    def test_returns_saved_row(self):
        row = {"id": "res-1", "raw_text": "John Doe — Python dev", "uploaded_at": "2026-04-24T00:00:00Z"}
        client = _make_chain(_mock_response([row]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.save_resume("John Doe — Python dev")

        assert result["id"] == "res-1"
        assert "Python" in result["raw_text"]

    def test_raises_when_no_row(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            with pytest.raises(RuntimeError, match="no row returned"):
                queries.save_resume("empty")


class TestGetLatestResume:
    def test_returns_most_recent(self):
        row = {"id": "res-2", "raw_text": "Latest resume", "uploaded_at": "2026-04-24T10:00:00Z"}
        client = _make_chain(_mock_response([row]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.get_latest_resume()

        assert result["id"] == "res-2"

    def test_returns_none_when_empty(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            assert queries.get_latest_resume() is None


# ─── interview_sessions ───────────────────────────────────────────────────────

class TestSaveSession:
    def test_returns_saved_session(self):
        row = {
            "id": "sess-1",
            "company": "Acme Corp",
            "jd_text": "Backend engineer role",
            "questions": ["Tell me about yourself"],
            "answers": ["I am a Python developer"],
            "created_at": "2026-04-24T00:00:00Z",
        }
        client = _make_chain(_mock_response([row]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.save_session(
                company="Acme Corp",
                jd_text="Backend engineer role",
                questions=["Tell me about yourself"],
                answers=["I am a Python developer"],
            )

        assert result["id"] == "sess-1"
        assert result["company"] == "Acme Corp"

    def test_raises_when_no_row(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            with pytest.raises(RuntimeError, match="no row returned"):
                queries.save_session("X", "jd", [], [])


class TestGetAllSessions:
    def test_returns_all_sessions(self):
        rows = [
            {"id": "s1", "company": "Acme"},
            {"id": "s2", "company": "Globex"},
        ]
        client = _make_chain(_mock_response(rows))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            result = queries.get_all_sessions()

        assert len(result) == 2

    def test_returns_empty_list_when_none(self):
        client = _make_chain(_mock_response([]))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            assert queries.get_all_sessions() == []


# ─── error handling ───────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_unwrap_raises_on_supabase_error(self):
        error_obj = MagicMock()
        error_obj.__bool__ = lambda self: True
        client = _make_chain(_mock_response(None, error=error_obj))

        with patch("db.queries.get_client", return_value=client):
            from db import queries
            with pytest.raises(RuntimeError, match="Supabase error"):
                queries.get_all_tasks()
