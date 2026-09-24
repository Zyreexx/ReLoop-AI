"""
Health and readiness endpoints.
"""
from fastapi import APIRouter
from app.config import settings
from app.ai.gemini_client import gemini_client

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "ai_status": "live" if gemini_client.is_live else "deterministic_fallback",
        "engine": "deterministic_optimizer_v1",
    }
