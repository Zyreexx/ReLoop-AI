"""
Tests for condition profile building and evidence provenance preservation.
"""
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
    assert "Untested" in batt.label or "No diagnostic" in batt.observations[0]


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
