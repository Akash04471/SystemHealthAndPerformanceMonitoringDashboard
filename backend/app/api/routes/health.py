from fastapi import APIRouter

from ...core.config import get_settings
from ...core.db import is_database_available

router = APIRouter()


@router.get("/live")
def liveness() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def readiness() -> dict:
    settings = get_settings()
    return {
        "status": "ready",
        "environment": settings.app_env,
        "db_configured": bool(settings.db_user and settings.db_password),
        "redis_configured": bool(settings.redis_url),
        "db_connected": is_database_available(),
    }
