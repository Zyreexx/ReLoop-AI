"""
Tests for condition profile building, evidence provenance preservation,
strict rule enforcement, and route idempotency.
"""
from fastapi.testclient import TestClient
from app.db.store import store
from app.schemas.enums import EvidenceType, ConfidenceLevel, ComponentStatus, DeviceCategory
from app.schemas.evidence import EvidenceItem
from app.schemas.product import ProductRecord, ProductSpecs
from app.services.assessment_service import assessment_service


def test_photo_alone_does_not_prove_battery_health():
    """
    CRITICAL NON-NEGOTIABLE RULE:
    A photograph can NEVER prove internal battery/SSD/motherboard health.
    If only visual photos are provided, battery health must be UNKNOWN/Untested.
    """
    prod = ProductRecord(
        id="prod_test_photo_only",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
    )
    store.save_product(prod)

    # Only add visual evidence
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection: top_cover.jpg",
            component="chassis",
            value={"observation": "Clean aluminum casing with no cracks."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    batt = profile.get_component("battery")

    assert batt is not None
    assert batt.status == ComponentStatus.UNKNOWN
    assert "Untested" in batt.label or "Insufficient evidence" in batt.observations[0]


def test_visual_evidence_never_sets_internal_components_status():
    """
    CRITICAL RULE:
    VISUAL evidence can NEVER set BATTERY, SSD, RAM, THERMALS, or SYSTEM status.
    """
    prod = ProductRecord(
        id="prod_test_visual_internal",
        manufacturer="Lenovo",
        model="ThinkPad T14",
        model_year=2020,
    )
    store.save_product(prod)

    # Attempt to inject visual evidence on internal components
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Photo inspection: internal_look.jpg",
            component="battery",
            value={"visible_status": "GOOD", "observation": "Battery pouch looks intact"},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Photo inspection: ssd_sticker.jpg",
            component="ssd",
            value={"visible_status": "GOOD", "observation": "SSD label is clean"},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Photo inspection: ram_heatsink.jpg",
            component="ram",
            value={"visible_status": "GOOD", "observation": "RAM stick seated in slot"},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Photo inspection: fan_grill.jpg",
            component="thermals",
            value={"visible_status": "GOOD", "observation": "Fan grill looks dust-free"},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Photo inspection: motherboard.jpg",
            component="system",
            value={"visible_status": "GOOD", "observation": "Motherboard looks unburnt"},
        ),
    )

    profile = assessment_service.build_profile(prod.id)

    # Every internal component must remain UNKNOWN despite visual evidence
    for comp_name in ["battery", "ssd", "ram", "thermals", "system"]:
        comp = profile.get_component(comp_name)
        assert comp is not None
        assert comp.status == ComponentStatus.UNKNOWN, f"{comp_name} was set to {comp.status} by visual evidence!"
        assert "Untested" in comp.label
        assert any("Insufficient evidence" in obs for obs in comp.observations)


def test_user_reported_evidence_alone_never_produces_good():
    """
    CRITICAL RULE:
    USER_REPORTED evidence alone can NEVER produce a GOOD status.
    """
    prod = ProductRecord(
        id="prod_test_user_reported_only",
        manufacturer="HP",
        model="EliteBook 840 G7",
        model_year=2020,
    )
    store.save_product(prod)

    # Add user reported evidence
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.USER_REPORTED,
            source="User intake survey",
            component="battery",
            value={"user_statement": "Battery seems fine to me", "reported_issues": []},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.USER_REPORTED,
            source="User intake survey",
            component="ssd",
            value={"user_statement": "Storage works okay", "reported_issues": []},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.USER_REPORTED,
            source="User intake survey",
            component="ram",
            value={"user_statement": "RAM has no crashes", "reported_issues": []},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.USER_REPORTED,
            source="User intake survey",
            component="thermals",
            value={"user_statement": "Loud fan noise when running video", "reported_issues": ["Hot laptop"]},
        ),
    )

    profile = assessment_service.build_profile(prod.id)

    for comp_name in ["battery", "ssd", "ram", "thermals"]:
        comp = profile.get_component(comp_name)
        assert comp is not None
        assert comp.status != ComponentStatus.GOOD, f"{comp_name} was marked GOOD from user-reported evidence alone!"
        assert comp.status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.FAIR, ComponentStatus.UNKNOWN]


def test_missing_evidence_yields_unknown_with_insufficient_evidence():
    """
    CRITICAL RULE:
    Missing evidence yields UNKNOWN status with 'Insufficient evidence' in observations.
    """
    prod = ProductRecord(
        id="prod_test_empty_evidence",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
    )
    store.save_product(prod)

    profile = assessment_service.build_profile(prod.id)

    # All components should be UNKNOWN / Untested
    for comp_name in ["battery", "ssd", "ram", "thermals", "display", "keyboard", "chassis", "system"]:
        comp = profile.get_component(comp_name)
        assert comp is not None, f"Missing component {comp_name}"
        assert comp.status == ComponentStatus.UNKNOWN
        assert "Untested" in comp.label
        assert any("Insufficient evidence" in obs for obs in comp.observations)


def test_condition_profile_preserves_provenance():
    prod = ProductRecord(
        id="prod_test_prov",
        manufacturer="Lenovo",
        model="ThinkPad T490",
        model_year=2019,
        specs=ProductSpecs(category=DeviceCategory.LAPTOP),
    )
    store.save_product(prod)

    # Add diagnostic evidence
    diag_ev = EvidenceItem(
        id="ev_diag_123",
        type=EvidenceType.DIAGNOSTIC,
        source="HWInfo Battery Report",
        component="battery",
        value={"health_percentage": 78.5, "cycle_count": 520, "design_capacity_mwh": 50000.0, "full_charge_capacity_mwh": 39250.0},
    )
    store.add_evidence(prod.id, diag_ev)

    # Add visual evidence
    vis_ev = EvidenceItem(
        id="ev_vis_456",
        type=EvidenceType.VISUAL,
        source="Optical Scan: keyboard.jpg",
        component="keyboard",
        value={"visible_status": "SERVICE_REQUIRED", "observation": "Broken spacebar retainer hinge"},
    )
    store.add_evidence(prod.id, vis_ev)

    profile = assessment_service.build_profile(prod.id)

    # Check battery condition
    batt = profile.get_component("battery")
    assert batt.status == ComponentStatus.SERVICE_REQUIRED
    assert "ev_diag_123" in batt.evidence_ids
    assert "HWInfo Battery Report" in batt.evidence_sources

    # Check keyboard condition
    kb = profile.get_component("keyboard")
    assert kb.status == ComponentStatus.SERVICE_REQUIRED
    assert "ev_vis_456" in kb.evidence_ids


def test_assessment_route_idempotency(client: TestClient):
    """
    Test that POST /api/assessment/build is idempotent:
    Resubmitting the same assessment overwrites/updates the existing profile without duplicating.
    """
    # Create product
    create_res = client.post(
        "/api/products",
        json={
            "manufacturer": "Dell",
            "model": "Latitude 5420",
            "model_year": 2021,
            "category": "LAPTOP",
        },
    )
    prod_id = create_res.json()["id"]

    # Submit diagnostics
    client.post(
        "/api/diagnostics/validate",
        json={
            "product_id": prod_id,
            "battery": {
                "design_capacity_mwh": 54000.0,
                "full_charge_capacity_mwh": 39420.0,
                "cycle_count": 680,
            },
        },
    )

    # Build assessment #1
    res1 = client.post("/api/assessment/build", json={"product_id": prod_id})
    assert res1.status_code == 200
    data1 = res1.json()

    # Build assessment #2 (resubmission)
    res2 = client.post("/api/assessment/build", json={"product_id": prod_id})
    assert res2.status_code == 200
    data2 = res2.json()

    # Confirm same product_id, same structure, no duplication
    assert data1["product_id"] == data2["product_id"]
    assert len(data1["components"]) == len(data2["components"])
    assert data1["components"]["battery"]["status"] == data2["components"]["battery"]["status"]

    # GET endpoint retrieval
    get_res = client.get(f"/api/assessment/{prod_id}")
    assert get_res.status_code == 200
    assert get_res.json()["product_id"] == prod_id
