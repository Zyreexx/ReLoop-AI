"""
Symptoms schemas conforming to docs/architecture.md section 9:
POST /api/symptoms/parse
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.evidence import Evidence


class ParsedSymptomItem(BaseModel):
    component: str
    symptom: str
    severity: str = "MODERATE"
    user_statement: str


class SymptomsParseRequest(BaseModel):
    product_id: Optional[str] = None
    symptoms: List[str] = Field(default_factory=list)
    selected_symptoms: Optional[List[str]] = None
    notes: Optional[str] = None
    user_notes: Optional[str] = None
    intended_use: Optional[str] = Field(
        "daily_office_and_web",
        description="daily_office_and_web, student_learning, coding_development, media_light_use, backup_secondary"
    )
    daily_usage_hours: Optional[float] = Field(4.0, ge=0.0, le=24.0)

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values):
        if isinstance(values, dict):
            if not values.get("symptoms") and values.get("selected_symptoms"):
                values["symptoms"] = values["selected_symptoms"]
            elif not values.get("selected_symptoms") and values.get("symptoms"):
                values["selected_symptoms"] = values["symptoms"]

            if not values.get("notes") and values.get("user_notes"):
                values["notes"] = values["user_notes"]
            elif not values.get("user_notes") and values.get("notes"):
                values["user_notes"] = values["notes"]
        return values


class SymptomsParseResponse(BaseModel):
    product_id: Optional[str] = None
    parsed_symptoms: List[ParsedSymptomItem | Dict[str, Any]] = Field(default_factory=list)
    evidence_items: List[Evidence] = Field(default_factory=list)
    intended_use: str = "daily_office_and_web"


# Compatibility aliases
SymptomInput = SymptomsParseRequest
SymptomParseResult = SymptomsParseResponse
