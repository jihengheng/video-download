from fastapi import APIRouter

from app.api.routes_admin import router as admin_router
from app.api.routes_auth import router as auth_router
from app.api.routes_tasks import router as tasks_router
from app.api.routes_video import router as video_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(video_router)
api_router.include_router(tasks_router)
api_router.include_router(admin_router)
