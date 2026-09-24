"""
Vision schemas conforming to docs/architecture.md and prompt requirements:
VisibleFinding: component, description, severity, confidence, evidence_type (VISUAL)
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.enums import ComponentName, ComponentStatus, EvidenceType
from app.schemas.evidence import Evidence
from app.schemas.product import ProductCandidate


class VisibleFinding(BaseModel):
    component: ComponentName | str = Field(
        ...,
        description="DISPLAY, KEYBOARD, HINGE_CHASSIS, PORTS, CHASSIS"
    )
    description: str = Field(..., description="Observable exterior condition description")
    severity: str = Field("MODERATE", description="LOW, MODERATE, HIGH")
    confidence: float = Field(0.85, ge=0.0, le=1.0)
    evidence_type: EvidenceType = EvidenceType.VISUAL


class VisionAnalyzeRequest(BaseModel):
    product_id: str
    image_names: Optional[List[str]] = Field(default_factory=list)
    inspection_notes: Optional[str] = None


class VisionAnalyzeResponse(BaseModel):
    product_id: str
    findings: List[VisibleFinding] | Dict[str, Any] = Field(default_factory=list)
    overall_visual_condition: str = "GOOD"
    overall_condition: ComponentStatus = ComponentStatus.GOOD
    evidence_items: List[Evidence] = Field(default_factory=list)


# Aliases
VisionAnalysisRequest = VisionAnalyzeRequest
VisionAnalysisResponse = VisionAnalyzeResponse
VisualComponentFinding = VisibleFinding
