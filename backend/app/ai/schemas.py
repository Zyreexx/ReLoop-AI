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

