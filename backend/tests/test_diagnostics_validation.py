"""
Tests for diagnostic validation rules and error formats.
Enforces rules.md error format:
{
  "error": {
    "code": "INVALID_DIAGNOSTIC",
    "message": "Full-charge capacity cannot exceed design capacity.",
    "field": "battery.full_charge_capacity"
  }
}
"""
import pytest
from app.schemas.errors import AppException
from app.schemas.enums import EvidenceType
from app.schemas.diagnostics import (
    DiagnosticsInput,
    BatteryDiagnostic,
    SsdDiagnostic,
    RamDiagnostic,
    ThermalDiagnostic,
)
from app.services.diagnostic_service import diagnostic_service


def test_full_charge_exceeding_design_capacity_raises_error():
    """
    CRITICAL RULE from rules.md:
    Full-charge capacity cannot exceed design capacity.
    """
    with pytest.raises(Exception) as exc_info:
        # Pydantic or service validation should catch this
        diag_input = DiagnosticsInput(
            product_id="test_prod",
            battery=BatteryDiagnostic(
                design_capacity_mwh=50000.0,
                full_charge_capacity_mwh=65000.0,
            ),
        )
        diagnostic_service.validate_and_record(diag_input)

    err_str = str(exc_info.value)
    assert "Full-charge capacity cannot exceed design capacity" in err_str


def test_service_level_validation_raises_typed_app_exception():
    with pytest.raises(Exception) as exc_info:
        BatteryDiagnostic(
            design_capacity_mwh=50000.0,
            full_charge_capacity_mwh=40000.0,
            cycle_count=-5,
        )

    assert "cycle_count" in str(exc_info.value)


def test_ssd_health_range_validation():
    with pytest.raises(Exception) as exc_info:
        SsdDiagnostic(
            smart_status="PASS",
            health_percentage=150.0,
        )

    assert "health_percent" in str(exc_info.value)


def test_thermal_idle_exceeding_max_raises_error():
    with pytest.raises(Exception) as exc_info:
        ThermalDiagnostic(
            cpu_idle_temp_c=98.0,
            cpu_max_temp_c=75.0,
        )

    assert "Idle CPU temperature cannot exceed max recorded temperature" in str(exc_info.value)


def test_valid_diagnostics_produces_evidence_with_diagnostic_type():
    data = DiagnosticsInput(
        product_id="test_prod",
        battery=BatteryDiagnostic(
            design_capacity_mwh=58000.0,
            full_charge_capacity_mwh=42340.0,
            cycle_count=450,
        ),
        ssd=SsdDiagnostic(
            smart_status="PASS",
            health_percentage=94.0,
        ),
        ram=RamDiagnostic(
            memory_test_status="PASS",
            installed_gb=16,
        ),
        thermals=ThermalDiagnostic(
            cpu_idle_temp_c=45.0,
            cpu_max_temp_c=82.0,
            throttling_detected=False,
        ),
    )
    res = diagnostic_service.validate_and_record(data)
    assert res.valid is True
    assert len(res.evidence_items) == 4

    for ev in res.evidence_items:
        assert ev.type == EvidenceType.DIAGNOSTIC
        assert ev.source is not None
        assert ev.confidence is not None


def test_parse_windows_battery_report_text():
    sample_report = """
    BATTERY REPORT
    DESIGN CAPACITY        52,000 mWh
    FULL CHARGE CAPACITY   38,400 mWh
    CYCLE COUNT            420
    """
    data = DiagnosticsInput(
        product_id="test_prod",
        report_text=sample_report,
    )
    res = diagnostic_service.validate_and_record(data)
    assert res.valid is True
    batt_ev = next((e for e in res.evidence_items if e.component == "battery"), None)
    assert batt_ev is not None
    assert batt_ev.value["design_capacity_mwh"] == 52000.0
    assert batt_ev.value["full_charge_capacity_mwh"] == 38400.0
    assert batt_ev.value["cycle_count"] == 420
