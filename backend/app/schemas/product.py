"""
Product schemas conforming to docs/architecture.md section 6:
Product: id, manufacturer, model, model_year, category, serial_or_identifier, age
And section 9 endpoint contracts.
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4
from pydantic import BaseModel, Field, model_validator
from app.schemas.enums import DeviceCategory, ConfidenceLevel


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
    age: float = Field(..., ge=0.0, description="Product age in years")
    specs: ProductSpecs = Field(default_factory=ProductSpecs)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @model_validator(mode="before")
    @classmethod
    def populate_age_aliases(cls, values):
        if isinstance(values, dict):
            if "age" not in values and "age_years" in values:
                values["age"] = values["age_years"]
            elif "age" not in values and "model_year" in values:
                values["age"] = max(0.5, float(2026 - int(values["model_year"])))
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
    image_base64: Optional[List[str]] = Field(default_factory=list)
    hint: Optional[str] = None
    manual_model: Optional[str] = None
    model_id: Optional[str] = None
    serial_or_identifier: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def reconcile_hints(cls, values):
        if isinstance(values, dict):
            target = values.get("manual_model") or values.get("model_id") or values.get("hint")
            if target:
                if not values.get("manual_model"):
                    values["manual_model"] = target
                if not values.get("hint"):
                    values["hint"] = target
                if not values.get("model_id"):
                    values["model_id"] = target
        return values


class ProductIdentifyResponse(BaseModel):
    identified_model: Optional[ProductCandidate] = None
    is_supported: bool = True
    confidence: float = 0.85
    visible_label_text: Optional[str] = None
    visual_clues: List[str] = Field(default_factory=list)
    needs_confirmation: bool = True
    requires_user_confirmation: bool = True
    alternative_models: List[ProductCandidate] = Field(default_factory=list)
    supported_models: List[ProductCandidate] = Field(default_factory=list)
    message: Optional[str] = None



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
