"""
Vision service for physical exterior condition and visible damage assessment.
Strictly preserves VISUAL evidence provenance; never guesses internal health.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.ai.gemini_client import gemini_client
from app.db.store import store
from app.schemas.enums import EvidenceType, ConfidenceLevel
from app.schemas.evidence import EvidenceItem


class VisionAnalysisRequest(BaseModel):
    product_id: str
    image_names: Optional[List[str]] = Field(default_factory=list)
    inspection_notes: Optional[str] = None


class VisualComponentFinding(BaseModel):
    status: str
    observation: str


class VisionAnalysisResponse(BaseModel):
    product_id: str
    findings: Dict[str, VisualComponentFinding]
    overall_visual_condition: str
    evidence_items: List[EvidenceItem]


class VisionService:
    def analyze_visible_damage(self, req: VisionAnalysisRequest) -> VisionAnalysisResponse:
        ai_res = gemini_client.analyze_visible_damage(
            image_names=req.image_names,
            notes=req.inspection_notes or "",
        )

        findings: Dict[str, VisualComponentFinding] = {}
        evidence_items: List[EvidenceItem] = []

        for comp in ["display", "keyboard", "chassis", "ports"]:
            data = ai_res.get(comp, {"status": "GOOD", "observation": "No visible flaws observed."})
            findings[comp] = VisualComponentFinding(
                status=data.get("status", "GOOD"),
                observation=data.get("observation", ""),
            )
            ev = EvidenceItem(
                type=EvidenceType.VISUAL,
                source=f"Optical Inspection ({', '.join(req.image_names) if req.image_names else 'Uploaded photos'})",
                component=comp,
                value={
                    "observation": data.get("observation", ""),
                    "visible_status": data.get("status", "GOOD"),
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(req.product_id, ev)
            evidence_items.append(ev)

        return VisionAnalysisResponse(
            product_id=req.product_id,
            findings=findings,
            overall_visual_condition=ai_res.get("overall_visual_condition", "GOOD"),
            evidence_items=evidence_items,
        )


vision_service = VisionService()
