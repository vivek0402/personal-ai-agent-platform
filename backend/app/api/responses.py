"""Shared response shape: { success, data, error }."""
from typing import Any, Optional


def ok(data: Any = None) -> dict:
    return {"success": True, "data": data, "error": None}


def err(message: str, data: Any = None) -> dict:
    return {"success": False, "data": data, "error": message}
