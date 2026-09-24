"""
Re-export and compatibility layer for vision service.
"""
from app.services.vision import (
    VisionService,
    vision_service,
    filter_visible_findings,
    FORBIDDEN_INTERNAL_KEYWORDS,
)
from app.schemas.vision import (
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisualComponentFinding,
    VisibleFinding,
)

__all__ = [
    "VisionService",
    "vision_service",
    "filter_visible_findings",
    "FORBIDDEN_INTERNAL_KEYWORDS",
    "VisionAnalysisRequest",
    "VisionAnalysisResponse",
    "VisualComponentFinding",
    "VisibleFinding",
]
