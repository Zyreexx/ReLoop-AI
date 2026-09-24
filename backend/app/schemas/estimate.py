"""
Reusable Estimate model carrying strict uncertainty ranges, basis, and assumptions.
Supports both value_min/value_max and min_val/max_val aliases.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator


class Estimate(BaseModel):
    value_min: float = Field(..., description="Lower bound of estimate range")
    value_max: float = Field(..., description="Upper bound of estimate range")
    unit: str = Field(..., description="Unit of measurement (e.g. 'USD', 'years', 'kg CO2e', 'days')")
    basis: str = Field(..., description="Methodological basis (e.g. 'DATABASE', 'ESTIMATE', 'LIFECYCLE_MODEL')")
    assumptions: List[str] = Field(default_factory=list, description="Explicit technical and operational assumptions")

    # Optional display range
    display_range: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_min_max(cls, values):
        if isinstance(values, dict):
            if "value_min" not in values and "min_val" in values:
                values["value_min"] = values["min_val"]
            elif "min_val" not in values and "value_min" in values:
                values["min_val"] = values["value_min"]

            if "value_max" not in values and "max_val" in values:
                values["value_max"] = values["max_val"]
            elif "max_val" not in values and "value_max" in values:
                values["max_val"] = values["value_max"]
        return values

    @model_validator(mode="after")
    def populate_display(self):
        if not self.display_range:
            if self.unit.upper() == "USD":
                self.display_range = f"${int(self.value_min)}–${int(self.value_max)}"
            elif self.unit == "years":
                self.display_range = f"+{self.value_min}–{self.value_max} years"
            else:
                self.display_range = f"{self.value_min}–{self.value_max} {self.unit}"
        return self

    @property
    def min_val(self) -> float:
        return self.value_min

    @property
    def max_val(self) -> float:
        return self.value_max


# Backwards compatibility alias
RangeEstimate = Estimate
