"""
Stubs out heavy external packages before any app code is imported so the full
test suite runs offline without `pip install -r requirements.txt`.

Import order matters: this file is loaded by pytest before any test module.
"""
import sys
from types import ModuleType
from unittest.mock import MagicMock


def _stub(name: str, **attrs) -> MagicMock:
    """Register a named MagicMock in sys.modules and return it."""
    mod = MagicMock(spec=ModuleType(name))
    for k, v in attrs.items():
        setattr(mod, k, v)
    sys.modules[name] = mod
    return mod


# ── supabase ──────────────────────────────────────────────────────────────────
if "supabase" not in sys.modules:
    _Client = MagicMock()
    _stub("supabase", create_client=MagicMock(return_value=_Client), Client=_Client)

# ── groq ──────────────────────────────────────────────────────────────────────
if "groq" not in sys.modules:
    _stub("groq", Groq=MagicMock())

# ── apscheduler ───────────────────────────────────────────────────────────────
if "apscheduler" not in sys.modules:
    _sched_mod = _stub("apscheduler")
    _stub("apscheduler.schedulers")
    _stub("apscheduler.schedulers.background", BackgroundScheduler=MagicMock())
    _stub("apscheduler.triggers")
    _stub("apscheduler.triggers.date", DateTrigger=MagicMock())

# ── pydantic_settings ─────────────────────────────────────────────────────────
if "pydantic_settings" not in sys.modules:
    try:
        import pydantic_settings  # noqa: F401 — installed, nothing to do
    except ImportError:
        try:
            from pydantic import BaseModel

            class _BaseSettings(BaseModel):
                """Minimal BaseSettings shim for pydantic v2."""
                model_config: dict = {}  # type: ignore[assignment]

            ps = _stub(
                "pydantic_settings",
                BaseSettings=_BaseSettings,
                SettingsConfigDict=dict,
            )
        except Exception:
            _stub("pydantic_settings")
