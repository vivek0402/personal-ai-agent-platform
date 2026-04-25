from fastapi import APIRouter

from app.api import tasks, interview, webhooks

router = APIRouter()
router.include_router(tasks.router,     prefix="/tasks",     tags=["tasks"])
router.include_router(interview.router, prefix="/interview", tags=["interview"])
router.include_router(webhooks.router,  prefix="/webhooks",  tags=["webhooks"])
