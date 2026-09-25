"""
Evidence schemas preserving strict provenance across visual, diagnostic, user-reported, database, and estimate sources.
Conforms to docs/architecture.md section 6:
Evidence: id, product_id, type, source, value, confidence, timestamp
"""
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4
from pydantic import BaseModel, Field
from app.schemas.enums import EvidenceType, ConfidenceLevel


class Evidence(BaseModel):
    id: str = Field(default_factory=lambda: f"ev_{uuid4().hex[:10]}")
    product_id: Optional[str] = None
    type: EvidenceType
    source: str = Field(
        ...,
        description="Source reference (e.g. 'Photo inspection: top_cover.jpg', 'OS Battery Report', 'User questionnaire', 'Dell Latitude 5420 Spec Sheet', 'ReLoop Lifecycle Model')"
    )
    component: Optional[str] = Field(
        None,
        description="Target component: battery, ssd, ram, thermals, display, keyboard, chassis, system"
    )
    value: Any = Field(
        ...,
        description="Observed measurement, factual specification, or visual observation"
    )
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Compatibility alias
EvidenceItem = Evidence
