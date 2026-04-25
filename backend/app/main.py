import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.health import router as health_router
from app.api.router import router as api_router
from app.config import get_settings
from app.tools.scheduler import start_scheduler, stop_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AI Agent Platform",
        version="1.0.0",
        description="Task Tracker + Interview Prep — powered by Groq llama3-70b-8192",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Global exception handlers ─────────────────────────────────────────────

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        """Return pydantic validation errors in our standard { success, data, error } shape."""
        messages = "; ".join(
            f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}"
            for e in exc.errors()
        )
        return JSONResponse(
            status_code=422,
            content={"success": False, "data": None, "error": messages},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        """Catch-all — prevents raw 500 tracebacks from reaching the client."""
        logger.error(
            "Unhandled exception on %s %s: %s",
            request.method, request.url.path, exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={"success": False, "data": None, "error": "Internal server error"},
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    app.include_router(health_router)               # GET /health
    app.include_router(api_router, prefix="/api")   # /api/tasks, /api/interview, /api/webhooks

    return app


app = create_app()
