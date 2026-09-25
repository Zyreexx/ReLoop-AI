"""
Tests for Condition Report endpoints:
- GET /api/reports/{assessment_id}
- GET /api/reports/{assessment_id}/download
- NOT_FOUND handling for unknown IDs
- Verification across multiple demo cases
"""
import json
from fastapi.testclient import TestClient

from app.db.store import store
from app.schemas.enums import ComponentStatus, DeviceCategory, EvidenceType, Objective
from app.schemas.evidence import EvidenceItem
from app.schemas.product import ProductRecord, ProductSpecs
from app.services.assessment_service import assessment_service
from app.services.recommendation_service import recommendation_service


def test_get_report_healthy_demo_case(client: TestClient):
    """
    Test report generation and retrieval for Demo Case 1 (Healthy ThinkPad T14).
    """
    prod = ProductRecord(
        id="prod_demo_test_healthy",
        manufacturer="Lenovo",
        model="ThinkPad T14 Gen 1",
        model_year=2021,
        age=3.0,
        specs=ProductSpecs(category=DeviceCategory.LAPTOP, ram_modular=True, ssd_modular=True, battery_replaceable=True),
    )
    store.save_product(prod)

    # Add diagnostic evidence
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.DIAGNOSTIC,
            source="ThinkPad UEFI Diagnostics",
            component="battery",
            value={"health_percentage": 92.0, "cycle_count": 185, "full_charge_capacity_mwh": 46000.0},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.DIAGNOSTIC,
            source="SMART Storage Log",
            component="ssd",
            value={"health_percentage": 98.0, "smart_status": "PASS"},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.DIAGNOSTIC,
            source="MemTest86+",
            component="ram",
            value={"memory_test_status": "PASS", "installed_gb": 16},
        ),
    )

    # Build profile
    assessment_service.build_profile(prod.id)

    # Fetch report
    res = client.get(f"/api/reports/{prod.id}")
    assert res.status_code == 200
    report = res.json()

    assert report["product_id"] == prod.id
    assert report["product"]["manufacturer"] == "Lenovo"
    assert report["product"]["model"] == "ThinkPad T14 Gen 1"
    assert "battery" in report["condition_profile"]["components"]
    assert report["recommendation"]["selected_pathway"] in ["REUSE", "UPGRADE", "REFURBISH"]
    assert len(report["alternative_pathways"]) >= 3
    assert report["impact_estimates"]["ewaste_diverted_kg"] > 0
    assert report["impact_estimates"]["co2_avoided_kg_min"] > 0
    assert len(report["assumptions"]) > 0
    assert "disclaimer" in report
    assert "Demo baseline assumptions" in report["disclaimer"]
    assert "timestamp" in report


def test_get_report_repairable_demo_case(client: TestClient):
    """
    Test report generation and retrieval for Demo Case 2 (Repairable Dell Latitude 5420).
    """
    prod = ProductRecord(
        id="prod_demo_test_repairable",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        age=4.0,
        specs=ProductSpecs(category=DeviceCategory.LAPTOP, ram_modular=True, ssd_modular=True, battery_replaceable=True),
    )
    store.save_product(prod)

    # Add diagnostic & visual evidence
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.DIAGNOSTIC,
            source="Dell SupportAssist Battery Report",
            component="battery",
            value={"health_percentage": 73.0, "cycle_count": 680, "full_charge_capacity_mwh": 39400.0},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.DIAGNOSTIC,
            source="HWiNFO Thermal Sensor",
            component="thermals",
            value={"cpu_max_temp_c": 96.0, "throttling_detected": True},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical Scan: keyboard.jpg",
            component="keyboard",
            value={"visible_status": "SERVICE_REQUIRED", "observation": "2 missing keys (F4, Left Alt)"},
        ),
    )

    # Build profile
    assessment_service.build_profile(prod.id)

    # Fetch report
    res = client.get(f"/api/reports/{prod.id}")
    assert res.status_code == 200
    report = res.json()

    assert report["product_id"] == prod.id
    assert report["product"]["model"] == "Latitude 5420"
    assert report["recommendation"]["selected_pathway"] in ["REPAIR", "REFURBISH", "REUSE"]
    assert report["impact_estimates"]["life_extension_years_max"] >= 2.5
    assert len(report["data_gaps"]) >= 1  # Untested components (e.g. SSD, RAM unmeasured in this test)


def test_download_report_as_json_attachment(client: TestClient):
    """
    Test GET /api/reports/{assessment_id}/download returns a downloadable JSON file.
    """
    prod = ProductRecord(
        id="prod_demo_test_download",
        manufacturer="HP",
        model="EliteBook 840 G7",
        model_year=2020,
    )
    store.save_product(prod)
    assessment_service.build_profile(prod.id)

    res = client.get(f"/api/reports/{prod.id}/download")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    assert "attachment;" in res.headers["content-disposition"]
    assert f"reloop_report_{prod.id}.json" in res.headers["content-disposition"]

    # Verify downloadable content parses to valid report JSON
    payload = json.loads(res.text)
    assert payload["product_id"] == prod.id
    assert "condition_profile" in payload
    assert "impact_estimates" in payload
    assert "disclaimer" in payload


def test_report_unknown_id_returns_not_found(client: TestClient):
    """
    Test that requesting an unknown assessment ID returns typed 404 NOT_FOUND.
    """
    res = client.get("/api/reports/unknown_assessment_99999")
    assert res.status_code == 404
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"
    assert "assessment_id" in body["error"]["field"]

    # Also test download endpoint returns 404
    dl_res = client.get("/api/reports/unknown_assessment_99999/download")
    assert dl_res.status_code == 404
    dl_body = dl_res.json()
    assert dl_body["error"]["code"] == "NOT_FOUND"
