"""
Product schemas conforming to docs/architecture.md section 6:
Product: id, manufacturer, model, model_year, category, serial_or_identifier, age
And section 9 endpoint contracts.
"""
from datetime import datetime, timezone
from typing import List, Optional, Union, Dict, Any
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator
from app.schemas.enums import DeviceCategory, ConfidenceLevel, IdentificationStatus


class ProductSpecs(BaseModel):
    category: DeviceCategory = DeviceCategory.LAPTOP
    ram_modular: bool = True
    ssd_modular: bool = True
    battery_replaceable: bool = True
    display_size_inches: float = 14.0
    weight_kg: float = 1.5
    baseline_embodied_co2_kg: float = 280.0
    estimated_original_msrp_usd: float = 1100.0


class Product(BaseModel):
    """
    Core Product entity matching docs/architecture.md section 6:
    id, manufacturer, model, model_year, category, serial_or_identifier, age
    """
    id: str = Field(default_factory=lambda: f"prod_{uuid4().hex[:10]}")
    manufacturer: str
    model: str
    model_year: int
    category: DeviceCategory = DeviceCategory.LAPTOP
    serial_or_identifier: Optional[str] = None
    slug: Optional[str] = None
    age: float = Field(default=0.0, ge=0.0, description="Product age in years")
    specs: ProductSpecs = Field(default_factory=ProductSpecs)
    is_generic: bool = False
    is_generic_assessment: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def populate_age_aliases(cls, values):
        if isinstance(values, dict):
            if "age" not in values and "age_years" in values:
                values["age"] = values["age_years"]
            elif "age" not in values and "model_year" in values:
                values["age"] = max(0.5, float(2026 - int(values["model_year"])))
            if "is_generic" in values and "is_generic_assessment" not in values:
                values["is_generic_assessment"] = values["is_generic"]
            elif "is_generic_assessment" in values and "is_generic" not in values:
                values["is_generic"] = values["is_generic_assessment"]
        return values

    @property
    def age_years(self) -> float:
        return self.age


# Backwards compatibility alias
ProductRecord = Product


class ProductCandidate(BaseModel):
    manufacturer: str
    model: str
    model_year: int
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH
    specs: ProductSpecs = Field(default_factory=ProductSpecs)


class ProductIdentifyRequest(BaseModel):
    image_names: Optional[List[str]] = Field(default_factory=list)
    image_base64: Optional[Union[str, List[str]]] = Field(default_factory=list)
    image_roles: Optional[List[str]] = None
    hint: Optional[str] = None
    manual_model: Optional[str] = None
    model_id: Optional[str] = None
    serial_or_identifier: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_hints(cls, values):
        if isinstance(values, dict):
            b64 = values.get("image_base64")
            if isinstance(b64, str):
                values["image_base64"] = [b64]
            manual = values.get("manual_model") or values.get("model_id")
            if manual:
                if not values.get("manual_model"):
                    values["manual_model"] = manual
                if not values.get("model_id"):
                    values["model_id"] = manual
        return values


class ProductIdentifyResponse(BaseModel):
    status: IdentificationStatus = IdentificationStatus.IDENTIFIED
    identified_model: Optional[ProductCandidate] = None
    candidate_id: Optional[str] = None
    is_supported: bool = True
    confidence: float = 0.85
    confidence_level: Optional[ConfidenceLevel] = None
    visible_label_text: Optional[str] = None
    visual_clues: List[str] = Field(default_factory=list)
    label_evidence: List[str] = Field(default_factory=list)
    visual_evidence: List[str] = Field(default_factory=list)
    contradictions: List[str] = Field(default_factory=list)
    needs_confirmation: bool = True
    requires_user_confirmation: bool = True
    alternative_models: List[ProductCandidate] = Field(default_factory=list)
    supported_models: List[ProductCandidate] = Field(default_factory=list)
    generic_fallback_available: bool = True
    generic_model: Optional[ProductCandidate] = None
    message: Optional[str] = None
    source: str = Field("live", description="live | sample-data | manual")
    is_laptop: bool = True
    device_category: Optional[str] = "LAPTOP"
    allow_manual_selection: bool = True
    display_faults: List[str] = Field(default_factory=list)
    keyboard_faults: List[str] = Field(default_factory=list)
    port_faults: List[str] = Field(default_factory=list)
    chassis_faults: List[str] = Field(default_factory=list)
    components_inspected_clean: List[str] = Field(default_factory=list)
    components_not_assessable: List[str] = Field(default_factory=list)
    visible_observations: List[Dict[str, Any]] = Field(default_factory=list)
    damage_findings: List[Dict[str, Any]] = Field(default_factory=list)
    overall_visual_condition: str = "GOOD"



# Aliases
ProductIdentificationRequest = ProductIdentifyRequest
ProductIdentificationResponse = ProductIdentifyResponse


class ProductCreate(BaseModel):
    manufacturer: str
    model: str
    model_year: int
    category: DeviceCategory = DeviceCategory.LAPTOP
    serial_or_identifier: Optional[str] = None
    age: Optional[float] = None
    age_years: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def sync_age(cls, values):
        if isinstance(values, dict):
            if values.get("age") is None and values.get("age_years") is not None:
                values["age"] = values["age_years"]
        return values
