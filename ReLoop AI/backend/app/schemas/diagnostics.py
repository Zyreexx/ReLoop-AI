"""
Diagnostics schemas and validations for battery, storage, memory, thermals, and system.
Conforms to docs/architecture.md and prompt requirements:
- battery: design_capacity, full_charge_capacity, cycle_count
- ssd: health_percent
- ram: test_result (PASS/FAIL)
- thermals: max_temp_c, throttling_detected
- system: critical_errors (list[str])
"""
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.evidence import Evidence


class BatteryDiagnostic(BaseModel):
    design_capacity: Optional[float] = Field(None, ge=100.0, le=200000.0)
    full_charge_capacity: Optional[float] = Field(None, ge=0.0, le=200000.0)
    cycle_count: Optional[int] = Field(None, ge=0, le=10000)
    health_percent: Optional[float] = Field(None, ge=0.0, le=100.0)

    # Aliases
    design_capacity_mwh: Optional[float] = None
    full_charge_capacity_mwh: Optional[float] = None
    health_percentage: Optional[float] = None

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values):
        if isinstance(values, dict):
            if "design_capacity" not in values and "design_capacity_mwh" in values:
                values["design_capacity"] = values["design_capacity_mwh"]
            elif "design_capacity_mwh" not in values and "design_capacity" in values:
                values["design_capacity_mwh"] = values["design_capacity"]

            if "full_charge_capacity" not in values and "full_charge_capacity_mwh" in values:
                values["full_charge_capacity"] = values["full_charge_capacity_mwh"]
            elif "full_charge_capacity_mwh" not in values and "full_charge_capacity" in values:
                values["full_charge_capacity_mwh"] = values["full_charge_capacity"]

            if "health_percent" not in values and "health_percentage" in values:
                values["health_percent"] = values["health_percentage"]
            elif "health_percentage" not in values and "health_percent" in values:
                values["health_percentage"] = values["health_percent"]
        return values

    @model_validator(mode="after")
    def validate_capacities(self):
        d_cap = self.design_capacity or self.design_capacity_mwh
        f_cap = self.full_charge_capacity or self.full_charge_capacity_mwh
        if d_cap is not None and f_cap is not None:
            if f_cap > d_cap:
                raise ValueError("Full-charge capacity cannot exceed design capacity.")
            if self.health_percent is None and d_cap > 0:
                calc_health = round((f_cap / d_cap) * 100.0, 1)
                self.health_percent = calc_health
                self.health_percentage = calc_health
        return self


class SsdDiagnostic(BaseModel):
    health_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    smart_status: Optional[str] = Field("PASS", description="PASS, WARNING, FAIL")
    health_percentage: Optional[float] = None
    capacity_gb: Optional[int] = Field(None, ge=16, le=16384)
    power_on_hours: Optional[int] = Field(None, ge=0)
    total_bytes_written_tb: Optional[float] = Field(None, ge=0.0)

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values):
        if isinstance(values, dict):
            if "health_percent" not in values and "health_percentage" in values:
                values["health_percent"] = values["health_percentage"]
            elif "health_percentage" not in values and "health_percent" in values:
                values["health_percentage"] = values["health_percent"]
        return values


class RamDiagnostic(BaseModel):
    test_result: Literal["PASS", "FAIL", "UNKNOWN"] = "PASS"
    installed_gb: Optional[int] = Field(None, ge=2, le=256)
    slots_used: Optional[int] = Field(None, ge=1, le=8)
    total_slots: Optional[int] = Field(None, ge=1, le=8)
    memory_test_status: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values):
        if isinstance(values, dict):
            if "test_result" not in values and "memory_test_status" in values:
                val = str(values["memory_test_status"]).upper()
                values["test_result"] = val if val in ["PASS", "FAIL", "UNKNOWN"] else "PASS"
            elif "memory_test_status" not in values and "test_result" in values:
                values["memory_test_status"] = values["test_result"]
        return values


class ThermalDiagnostic(BaseModel):
    max_temp_c: Optional[float] = Field(None, ge=10.0, le=130.0)
    throttling_detected: bool = False
    cpu_idle_temp_c: Optional[float] = Field(None, ge=10.0, le=120.0)
    cpu_max_temp_c: Optional[float] = None
    fan_noise_abnormal: Optional[bool] = False
    service_recommended: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, values):
        if isinstance(values, dict):
            if "max_temp_c" not in values and "cpu_max_temp_c" in values:
                values["max_temp_c"] = values["cpu_max_temp_c"]
            elif "cpu_max_temp_c" not in values and "max_temp_c" in values:
                values["cpu_max_temp_c"] = values["max_temp_c"]
        return values

    @model_validator(mode="after")
    def validate_temperatures(self):
        max_t = self.max_temp_c or self.cpu_max_temp_c
        idle_t = self.cpu_idle_temp_c
        if idle_t is not None and max_t is not None and idle_t > max_t:
            raise ValueError("Idle CPU temperature cannot exceed max recorded temperature.")
        return self


class SystemDiagnostic(BaseModel):
    critical_errors: List[str] = Field(default_factory=list)
    post_successful: bool = True
    motherboard_power_stable: bool = True


class DiagnosticsValidateRequest(BaseModel):
    product_id: Optional[str] = None
    report_text: Optional[str] = None
    battery: Optional[BatteryDiagnostic] = None
    ssd: Optional[SsdDiagnostic] = None
    ram: Optional[RamDiagnostic] = None
    thermals: Optional[ThermalDiagnostic] = None
    system: Optional[SystemDiagnostic] = None


class DiagnosticsValidateResponse(BaseModel):
    valid: bool
    evidence_items: List[Evidence] = Field(default_factory=list)
    summary: dict = Field(default_factory=dict)


# Compatibility aliases
DiagnosticsInput = DiagnosticsValidateRequest
DiagnosticValidationResult = DiagnosticsValidateResponse
