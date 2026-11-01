"""
Pydantic schemas for ReLoop Next-Life Engine.
Strictly conforms to the ReLoop AI Decision Matrix and JSON output schema.
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

CosmeticGrade = Literal["Grade A", "Grade B", "Grade C", "Grade D"]

NextLifeAction = Literal[
    "Resell / Refurbish",
    "Repurpose as Headless Server",
    "Convert to Lightweight OS",
    "Component Salvage",
    "E-Waste Recycling",
]


class DeviceSummary(BaseModel):
    detected_model: str = Field(
        ...,
        description="Identified laptop model or 'Generic Laptop'",
        example="Dell Latitude 5420",
    )
    cosmetic_grade: CosmeticGrade = Field(
        ...,
        description="Cosmetic Grade: Grade A | Grade B | Grade C | Grade D",
    )
    hardware_health_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Diagnostic hardware health score (0-100%)",
        example=85,
    )
    reloop_circular_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Overall circular viability score (0-100%)",
        example=82,
    )


class NextLifeRecommendation(BaseModel):
    action: NextLifeAction = Field(
        ...,
        description="Optimal Next-Life circular action according to the Decision Matrix",
    )
    headline: str = Field(
        ...,
        description="Punchy 1-line recommendation title",
        example="Enterprise Certified Refurbishment for Secondary Market Resale",
    )
    justification: str = Field(
        ...,
        description="Clear reasoning connecting visual condition and diagnostic score to choice",
    )
    actionable_steps: List[str] = Field(
        ...,
        description="Actionable sequential steps to execute this path",
        example=[
            "Sanitize storage using NIST 800-88 cryptographic erase",
            "Clean chassis casing and re-apply thermal paste",
            "Recalibrate battery and prepare secondary market listing",
        ],
    )


class EnvironmentalImpact(BaseModel):
    e_waste_prevented_kg: float = Field(
        ...,
        ge=0.0,
        description="Estimated kilograms of e-waste diverted from landfill",
        example=1.4,
    )
    estimated_co2_offset_kg: float = Field(
        ...,
        ge=0.0,
        description="Estimated embodied CO2 kilograms avoided by extending life",
        example=245.0,
    )


class NextLifeResponse(BaseModel):
    device_summary: DeviceSummary
    cosmetic_observations: List[str] = Field(
        ...,
        description="Detailed visual cosmetic findings (screen, chassis, keys, ports)",
    )
    hardware_observations: List[str] = Field(
        ...,
        description="Diagnostic hardware findings (battery, SSD S.M.A.R.T, CPU/RAM)",
    )
    next_life_recommendation: NextLifeRecommendation
    environmental_impact: EnvironmentalImpact


class DiagnosticInputPayload(BaseModel):
    cpu: Optional[str] = "Intel Core i5-1145G7"
    ram_gb: Optional[float] = 16.0
    battery_max_capacity: Optional[float] = None
    battery_design_capacity: Optional[float] = None
    battery_wear_pct: Optional[float] = None
    battery_health_pct: Optional[float] = None
    ssd_smart_health_pct: Optional[float] = 95.0
    display_test_flags: Optional[Dict[str, Any]] = None
    chassis_condition: Optional[str] = None
    motherboard_functional: Optional[bool] = True
    has_modular_parts: Optional[bool] = True
    modular_components: Optional[List[str]] = Field(
        default_factory=lambda: ["RAM", "NVMe SSD", "Wi-Fi Card"]
    )


class NextLifeAnalysisRequest(BaseModel):
    detected_model: Optional[str] = "Dell Latitude 5420"
    cosmetic_grade_override: Optional[CosmeticGrade] = None
    cosmetic_notes: Optional[str] = None
    diagnostics: Optional[DiagnosticInputPayload] = None
    image_names: Optional[List[str]] = None
