"""
Integration and unit tests for Smart Diagnostics:
- Session lifecycle: create, poll status, submit
- 8 subsystems deterministic evaluation and fault severity
- Evidence generation and linking to Condition Profile
- Circular optimization eligibility response
- Agent download endpoint
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.store import store
from app.schemas.product import ProductRecord, ProductSpecs
from app.schemas.enums import ComponentStatus, PathwayType, ObjectiveType
from app.services.assessment_service import assessment_service
from app.optimizer.scorer import score_pathways

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_store():
    store.clear()
    yield
    store.clear()


def test_diagnostic_session_lifecycle():
    # 1. Register a product
    product = ProductRecord(
        id="prod-diag-001",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        category="LAPTOP",
        age=3.5,
        specs=ProductSpecs(
            battery_design_capacity_mwh=51000,
            battery_replaceable=True,
            ram_modular=True,
            ssd_modular=True,
        ),
    )
    store.save_product(product)

    # 2. Create diagnostic session
    res = client.post("/api/diagnostics/session", json={"product_id": "prod-diag-001"})
    assert res.status_code == 200
    session_data = res.json()
    assert "session_token" in session_data
    token = session_data["session_token"]
    assert session_data["status"] == "PENDING"
    assert session_data["product_id"] == "prod-diag-001"
    assert "battery" in session_data["subsystems_progress"]

    # 3. Poll status initially
    status_res = client.get(f"/api/diagnostics/session/{token}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "PENDING"

    # 4. Agent submits findings for all 8 subsystems
    payload = {
        "timestamp": "2026-03-01T12:00:00Z",
        "overall_status": "FAIR",
        "subsystems": {
            "battery": {
                "status": "FAULT_DETECTED",
                "component_status": "WEAR",
                "fault_severity": "MEDIUM",
                "faults": ["Battery health at 72.5% (service threshold: 80%)."],
                "evidence": {
                    "design_capacity_mwh": 51000.0,
                    "full_charge_capacity_mwh": 37000.0,
                    "cycle_count": 520,
                    "health_percentage": 72.5,
                },
                "source": "Windows PowerCfg & ACPI Battery Diagnostic",
                "observations": ["Battery retains 37,000 mWh out of 51,000 mWh design capacity (72.5%)."],
            },
            "ssd": {
                "status": "PASSED",
                "component_status": "GOOD",
                "fault_severity": "INFO",
                "faults": [],
                "evidence": {
                    "model": "PC SN730 NVMe WDC 512GB",
                    "smart_status": "PASS",
                    "health_percentage": 94.0,
                    "capacity_gb": 512,
                },
                "source": "Windows Storage Controller SMART Diagnostic",
                "observations": ["SMART operational status: PASS."],
            },
            "ram": {
                "status": "PASSED",
                "component_status": "GOOD",
                "fault_severity": "INFO",
                "faults": [],
                "evidence": {
                    "installed_gb": 16,
                    "slots_used": 2,
                    "total_slots": 2,
                    "test_result": "PASS",
                },
                "source": "Windows SMBIOS Physical Memory Telemetry",
                "observations": ["Installed physical RAM: 16 GB."],
            },
            "thermals": {
                "status": "FAULT_DETECTED",
                "component_status": "WEAR",
                "fault_severity": "MEDIUM",
                "faults": ["Firmware thermal throttling detected: CPU frequency constrained."],
                "evidence": {
                    "max_temp_c": 91.0,
                    "throttling_detected": True,
                    "service_recommended": True,
                },
                "source": "Windows ACPI Thermal & Kernel Power Monitor",
                "observations": ["Peak recorded thermal reading: 91.0°C."],
            },
            "cpu": {
                "status": "PASSED",
                "component_status": "GOOD",
                "fault_severity": "INFO",
                "faults": [],
                "evidence": {
                    "model": "11th Gen Intel Core i5-1145G7 @ 2.60GHz",
                    "cores": 4,
                    "threads": 8,
                },
                "source": "Windows Processor CIM Interface",
                "observations": ["Processor: 11th Gen Intel Core i5-1145G7."],
            },
            "display": {
                "status": "PASSED",
                "component_status": "GOOD",
                "fault_severity": "INFO",
                "faults": [],
                "evidence": {
                    "adapter": "Intel Iris Xe Graphics",
                    "resolution": "1920x1080",
                    "status": "OK",
                },
                "source": "Windows Video Controller Interface",
                "observations": ["GPU Adapter: Intel Iris Xe driving 1920x1080 @ 60Hz."],
            },
            "keyboard": {
                "status": "PASSED",
                "component_status": "GOOD",
                "fault_severity": "INFO",
                "faults": [],
                "evidence": {
                    "device": "Standard PS/2 Keyboard",
                    "status": "OK",
                },
                "source": "Windows Keyboard HID Controller",
                "observations": ["Keyboard controller: Standard PS/2 Keyboard."],
            },
            "chassis": {
                "status": "PASSED",
                "component_status": "GOOD",
                "fault_severity": "INFO",
                "faults": [],
                "evidence": {
                    "form_factor": "Standard Laptop",
                },
                "source": "Windows SMBIOS System Enclosure",
                "observations": ["Chassis form factor identified: Standard Laptop."],
            },
            "system": {
                "status": "PASSED",
                "component_status": "GOOD",
                "fault_severity": "INFO",
                "faults": [],
                "evidence": {
                    "manufacturer": "Dell Inc.",
                    "product": "0K3X20",
                    "bios_version": "1.14.0",
                    "post_successful": True,
                    "motherboard_power_stable": True,
                    "uefi_post_status": "PASS",
                },
                "source": "Windows UEFI SMBIOS & WHEA Diagnostics",
                "observations": ["Motherboard: Dell Inc. 0K3X20 (POST OK)."],
            },
        },
        "faults": [
            {
                "component": "battery",
                "severity": "MEDIUM",
                "description": "Battery health at 72.5% (service threshold: 80%).",
            },
            {
                "component": "thermals",
                "severity": "MEDIUM",
                "description": "Firmware thermal throttling detected: CPU frequency constrained.",
            },
        ],
    }

    sub_res = client.post(f"/api/diagnostics/session/{token}/submit", json=payload)
    assert sub_res.status_code == 200
    report = sub_res.json()
    assert report["status"] == "COMPLETED"
    assert report["overall_hardware_health"] == "FAIR"
    assert "battery" in report["subsystems"]
    assert report["subsystems"]["battery"]["component_status"] == "WEAR"
    assert len(report["faults"]) == 2
    assert report["ai_explanation"] is not None

    # 5. Check session status polling after completion
    poll_res = client.get(f"/api/diagnostics/session/{token}/status")
    assert poll_res.status_code == 200
    assert poll_res.json()["status"] == "COMPLETED"

    # 6. Verify evidence was recorded in backend store
    ev_list = store.get_evidence("prod-diag-001")
    assert len(ev_list) >= 7
    batt_ev = next(e for e in ev_list if e.component == "battery")
    assert batt_ev.value["health_percentage"] == 72.5
    thm_ev = next(e for e in ev_list if e.component == "thermals")
    assert thm_ev.value["throttling_detected"] is True

    # 7. Synthesize Condition Profile via Assessment Service
    profile = assessment_service.build_profile("prod-diag-001")
    assert profile.product_id == "prod-diag-001"
    assert profile.components["battery"].status == ComponentStatus.SERVICE_REQUIRED
    assert profile.components["thermals"].status == ComponentStatus.SERVICE_REQUIRED
    assert profile.components["ssd"].status == ComponentStatus.GOOD
    assert profile.components["ram"].status == ComponentStatus.GOOD
    assert profile.components["system"].status == ComponentStatus.GOOD

    # 8. Verify Circular Optimization Scorer receives component profile
    score_result = score_pathways(product, profile, ObjectiveType.MAXIMUM_LIFE)
    assert score_result.selected_pathway in [PathwayType.REPAIR, PathwayType.REFURBISH]
    assert score_result.primary_recommendation is not None
    assert score_result.score > 0.0


def test_agent_download_endpoint():
    res = client.get("/api/diagnostics/agent/download")
    assert res.status_code == 200
    assert "ReLoop AI" in res.text or "diagnostics_agent" in res.text
