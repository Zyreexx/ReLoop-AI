"""
Vision schemas conforming to docs/architecture.md section 9:
POST /api/vision/analyze
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.evidence import Evidence


class VisualComponentFinding(BaseModel):
    status: str
    observation: str


class VisionAnalyzeRequest(BaseModel):
    product_id: str
    image_names: Optional[List[str]] = Field(default_factory=list)
    image_urls: Optional[List[str]] = Field(default_factory=list)
    image_base64: Optional[List[str]] = Field(default_factory=list)
    inspection_notes: Optional[str] = None


class VisionAnalyzeResponse(BaseModel):
    product_id: str
    findings: Dict[str, VisualComponentFinding | Dict[str, Any]]
    overall_visual_condition: str
    evidence_items: List[Evidence]


# Compatibility aliases
VisionAnalysisRequest = VisionAnalyzeRequest
VisionAnalysisResponse = VisionAnalyzeResponse
