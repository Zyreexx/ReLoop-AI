"""
Recommendation schemas conforming to docs/architecture.md section 6:
Recommendation: selected_pathway, objective, score, alternative_pathways, reasoning, evidence_ids, assumptions
And section 9 POST /api/recommendations/generate and GET /api/reports/{id}.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator
from app.schemas.enums import Objective, PathwayType
from app.schemas.pathway import Pathway


class ScoredPathway(BaseModel):
    pathway: Pathway
    score: float = Field(..., ge=0.0, le=100.0)
    rank: int = 1
    normalized_subscores: Dict[str, float] = Field(default_factory=dict)


class SecondLifeSuggestion(BaseModel):
    suggested_role: str
    target_user: str
    os_recommendation: str
    workloads: List[str]
    basis: str = "SPEC_MATCHING_HEURISTIC"


class ComponentRecoveryManifest(BaseModel):
    recoverable_parts: List[str] = Field(default_factory=list)
    salvage_value_estimate_usd: float = 0.0
    material_recovery_action: str = "Harvest modular RAM, SSD, and display panel for spare inventory."


class Recommendation(BaseModel):
    """
    Recommendation model matching docs/architecture.md section 6:
    selected_pathway, objective, score, alternative_pathways, reasoning, evidence_ids, assumptions
    """
    id: str = Field(default_factory=lambda: f"rec_{uuid4().hex[:10]}")
    product_id: Optional[str] = None
    selected_pathway: PathwayType
    objective: Objective
    score: float = Field(..., ge=0.0, le=100.0)
    alternative_pathways: List[ScoredPathway | Pathway | Any] = Field(default_factory=list)
    reasoning: List[str] = Field(
        default_factory=list,
        description="Clear, fact-based bullet points derived directly from verified evidence"
    )
    evidence_ids: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)

    # UI and enrichment helpers
    primary_recommendation: Optional[ScoredPathway] = None
    linked_evidence_ids: Optional[List[str]] = None
    explicit_assumptions: Optional[List[str]] = None
    second_life: Optional[SecondLifeSuggestion] = None
    component_recovery: Optional[ComponentRecoveryManifest] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values):
        if isinstance(values, dict):
            # Sync evidence_ids and linked_evidence_ids
            if "evidence_ids" not in values and "linked_evidence_ids" in values:
                values["evidence_ids"] = values["linked_evidence_ids"]
            elif "linked_evidence_ids" not in values and "evidence_ids" in values:
                values["linked_evidence_ids"] = values["evidence_ids"]

            # Sync assumptions and explicit_assumptions
            if "assumptions" not in values and "explicit_assumptions" in values:
                values["assumptions"] = values["explicit_assumptions"]
            elif "explicit_assumptions" not in values and "assumptions" in values:
                values["explicit_assumptions"] = values["assumptions"]

            # Extract score from primary_recommendation if not set
            if "score" not in values and values.get("primary_recommendation"):
                pr = values["primary_recommendation"]
                if hasattr(pr, "score"):
                    values["score"] = pr.score
                elif isinstance(pr, dict) and "score" in pr:
                    values["score"] = pr["score"]
            if "score" not in values:
                values["score"] = 85.0
        return values


# Endpoints Request/Response from section 9
class RecommendationsGenerateRequest(BaseModel):
    product_id: str
    objective: Objective = Objective.MAX_LIFE
    condition_profile_override: Optional[dict] = None


class RecommendationsGenerateResponse(Recommendation):
    pass


class ReportResponse(Recommendation):
    pass


# Compatibility aliases
RecommendationRequest = RecommendationsGenerateRequest
RecommendationResponse = Recommendation

Recommendation.model_rebuild()

