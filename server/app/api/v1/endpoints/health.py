from fastapi import APIRouter
from datetime import datetime
from server.app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": settings.VERSION,
        "timestamp": datetime.utcnow().isoformat(),
    }
