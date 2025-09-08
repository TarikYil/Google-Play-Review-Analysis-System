from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/")
async def health_check():
    """Servis sağlık kontrolü"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "export"
    }

@router.get("/ready")
async def readiness_check():
    """Servis hazırlık kontrolü"""
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "service": "export"
    }
