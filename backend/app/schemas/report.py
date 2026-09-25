"""
Condition report schemas conforming to docs/architecture.md section 6 and 9:
Combines product, condition profile, recommendations, alternatives with reasons,
impact estimates, assumptions, data gaps, disclaimer, and timestamp.
"""
from datetime import datetime, timezone
from typing import Any, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field

from app.schemas.condition import ConditionProfile
from app.schemas.product import Product
from app.schemas.recommendation import Recommendation, RecommendationExplanation, ScoredPathway


class ReportImpactEstimates(BaseModel):
    co2_avoided_kg_min: float = 0.0
    co2_avoided_kg_max: float = 0.0
    ewaste_diverted_kg: float = 0.0
    life_extension_years_min: float = 0.0
    life_extension_years_max: float = 0.0
    estimated_cost_min: float = 0.0
    estimated_cost_max: float = 0.0
    value_retained_percentage: float = 0.0
    material_retained_percentage: float = 0.0


class ConditionReportResponse(BaseModel):
    id: str = Field(default_factory=lambda: f"rep_{uuid4().hex[:10]}")
    assessment_id: str
    product_id: str
    product: Product
    condition_profile: ConditionProfile
    recommendation: Recommendation
    alternative_pathways: List[ScoredPathway | Any] = Field(default_factory=list)
    impact_estimates: ReportImpactEstimates
    assumptions: List[str] = Field(default_factory=list)
    data_gaps: List[str] = Field(default_factory=list)
    explanation: Optional[RecommendationExplanation] = None
    disclaimer: str = "Demo baseline assumptions, not verified market data. Estimates are derived from deterministic model parameters."
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# Compatibility alias
ReportPayload = ConditionReportResponse
