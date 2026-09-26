"""
Route registration for ReLoop AI.
"""
from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router
from app.api.routes.vision import router as vision_router
from app.api.routes.diagnostics import router as diagnostics_router
from app.api.routes.symptoms import router as symptoms_router
from app.api.routes.assessment import router as assessment_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.reports import router as reports_router
from app.api.routes.auth import router as auth_router


api_router = APIRouter(prefix="/api")
api_router.include_router(auth_router)
api_router.include_router(health_router)
api_router.include_router(products_router)
api_router.include_router(vision_router)
api_router.include_router(diagnostics_router)
api_router.include_router(symptoms_router)
api_router.include_router(assessment_router)
api_router.include_router(recommendations_router)
api_router.include_router(reports_router)

__all__ = ["api_router"]
