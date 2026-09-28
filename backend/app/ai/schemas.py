"""
Pydantic schemas for structured AI outputs from Gemini.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class ModelIdentificationOutput(BaseModel):
    model_name: str = Field(..., description="Exact matched model name or 'unknown'")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    visible_label_text: Optional[str] = Field(None, description="Directly read text from stickers/chassis")
    visual_clues: List[str] = Field(default_factory=list, description="Visual characteristics observed")


class CatalogIdentificationOutput(BaseModel):
    candidate_id: str = Field(..., description="Selected catalog candidate ID (e.g. C1, C2) or 'UNKNOWN'")
    label_evidence: List[str] = Field(default_factory=list, description="Text literally read from logos, badges, and labels")
    visual_evidence: List[str] = Field(default_factory=list, description="Observed visual features and design clues")
    contradictions: List[str] = Field(default_factory=list, description="Visual contradictions or mismatching indicators")
    model_confidence: float = Field(0.0, ge=0.0, le=1.0, description="Advisory raw model confidence score")


class DamageAssessmentOutput(BaseModel):
    cracks: List[str] = Field(default_factory=list)
    dents: List[str] = Field(default_factory=list)
    missing_keys: List[str] = Field(default_factory=list)
    hinge_damage: List[str] = Field(default_factory=list)
    port_damage: List[str] = Field(default_factory=list)
    visible_swelling: List[str] = Field(default_factory=list)
    observations: List[str] = Field(default_factory=list)


class SymptomClassificationOutput(BaseModel):
    matched_symptom_tags: List[str] = Field(default_factory=list)
    user_summary: Optional[str] = None


class ExplanationOutput(BaseModel):
    summary: str = Field(..., description="Executive narrative summary of the circular recommendation")
    details: List[str] = Field(default_factory=list, description="Supporting bullet points grounded in verified evidence")
    assumptions: List[str] = Field(default_factory=list, description="Explicit notes of key assumptions")

