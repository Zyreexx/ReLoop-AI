"""
Pathway schemas conforming to docs/architecture.md section 6:
Pathway: type, eligibility, estimated_cost, expected_life_extension, value_retained, material_retained, environmental_estimate, logistics, assumptions
"""
from typing import Any, List, Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.enums import PathwayType
from app.schemas.estimate import Estimate, RangeEstimate


class EnvironmentalEstimate(BaseModel):
    co2_avoided_kg_min: float
    co2_avoided_kg_max: float
    ewaste_diverted_kg: float
    basis: str = "LIFECYCLE_EMISSION_BENCHMARK"
    assumptions: List[str] = Field(default_factory=list)


class LogisticsEstimate(BaseModel):
    complexity: str = Field("MODERATE", description="LOW, MODERATE, HIGH")
    turnaround_days_min: int = 1
    turnaround_days_max: int = 5
    basis: str = "SERVICE_BENCHMARK"
    assumptions: List[str] = Field(default_factory=list)


class PathwayEligibility(BaseModel):
    is_eligible: bool
    reasons: List[str] = Field(default_factory=list)
    ineligibility_reasons: List[str] = Field(default_factory=list)


class Pathway(BaseModel):
    """
    Core Pathway model matching docs/architecture.md section 6:
    type, eligibility, estimated_cost, expected_life_extension, value_retained, material_retained, environmental_estimate, logistics, assumptions
    """
    type: PathwayType
    eligibility: PathwayEligibility | bool | Any
    estimated_cost: Estimate
    expected_life_extension: Estimate
    value_retained: float = Field(..., ge=0.0, le=100.0, description="Percentage of original value retained")
    material_retained: float = Field(..., ge=0.0, le=100.0, description="Percentage of material retained in loop")
    environmental_estimate: EnvironmentalEstimate | Estimate | Any
    logistics: LogisticsEstimate | Estimate | Any
    assumptions: List[str] = Field(default_factory=list)

    # Optional UI enrichment fields
    title: Optional[str] = None
    summary: Optional[str] = None
    actions_required: List[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values):
        if isinstance(values, dict):
            # Sync expected_life_extension / expected_life_extension_years
            if "expected_life_extension" not in values and "expected_life_extension_years" in values:
                values["expected_life_extension"] = values["expected_life_extension_years"]
            elif "expected_life_extension_years" not in values and "expected_life_extension" in values:
                values["expected_life_extension_years"] = values["expected_life_extension"]

            # Sync value_retained / value_retained_percentage
            if "value_retained" not in values and "value_retained_percentage" in values:
                values["value_retained"] = values["value_retained_percentage"]
            elif "value_retained_percentage" not in values and "value_retained" in values:
                values["value_retained_percentage"] = values["value_retained"]

            # Sync material_retained / material_retained_percentage
            if "material_retained" not in values and "material_retained_percentage" in values:
                values["material_retained"] = values["material_retained_percentage"]
            elif "material_retained_percentage" not in values and "material_retained" in values:
                values["material_retained_percentage"] = values["material_retained"]

            # Set title default if missing
            if not values.get("title") and values.get("type"):
                t_val = values.get("type")
                values["title"] = str(t_val).replace("_", " ").title()
        return values

    @property
    def expected_life_extension_years(self) -> Estimate:
        return self.expected_life_extension

    @property
    def value_retained_percentage(self) -> float:
        return self.value_retained

    @property
    def material_retained_percentage(self) -> float:
        return self.material_retained


# Backwards compatibility alias
PathwayOption = Pathway

Pathway.model_rebuild()

