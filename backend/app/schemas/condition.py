"""
Component condition schemas conforming to docs/architecture.md section 6:
ComponentCondition: component, status, observations, measurements, confidence, evidence_ids
And section 9 POST /api/assessment/build request/response.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.enums import ComponentName, ComponentStatus, ConfidenceLevel
from app.schemas.evidence import Evidence


class ComponentCondition(BaseModel):
    """
    ComponentCondition model matching docs/architecture.md section 6:
    component, status, observations, measurements, confidence, evidence_ids
    """
    component: ComponentName | str = Field(
        ...,
        description="BATTERY, SSD, RAM, THERMALS, DISPLAY, KEYBOARD, HINGE_CHASSIS, SYSTEM"
    )
    status: ComponentStatus
    observations: List[str] = Field(default_factory=list)
    measurements: Dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    evidence_ids: List[str] = Field(default_factory=list)

    # UI and optimization enrichment helpers
    label: Optional[str] = None
    evidence_sources: List[str] = Field(default_factory=list)
    repairable: bool = True
    upgradeable: bool = False

    @model_validator(mode="before")
    @classmethod
    def populate_label(cls, values):
        if isinstance(values, dict) and not values.get("label"):
            status_val = values.get("status")
            comp = values.get("component")
            values["label"] = f"{comp}: {status_val}"
        return values


class AssessmentBuildRequest(BaseModel):
    product_id: str


class AssessmentBuildResponse(BaseModel):
    product_id: str
    overall_hardware_health: str = Field("FAIR", description="GOOD, FAIR, DEGRADED, CRITICAL")
    components: Dict[str, ComponentCondition] = Field(default_factory=dict)
    all_evidence: List[Evidence] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def evidence_items(self) -> List[Evidence]:
        return self.all_evidence

    def get_component(self, name: str) -> Optional[ComponentCondition]:
        low = name.lower()
        for k, v in self.components.items():
            if k.lower() == low or (hasattr(v.component, "value") and v.component.value.lower() == low) or str(v.component).lower() == low:
                return v
        return None


# Backwards compatibility alias
ConditionProfile = AssessmentBuildResponse
BuildAssessmentRequest = AssessmentBuildRequest
