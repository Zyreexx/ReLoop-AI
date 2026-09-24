"""
Optical inspection and visible damage analysis routes.
"""
from fastapi import APIRouter
from app.services.vision_service import (
    vision_service,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
)

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.post("/analyze", response_model=VisionAnalysisResponse)
def analyze_visible_damage(req: VisionAnalysisRequest):
    return vision_service.analyze_visible_damage(req)
