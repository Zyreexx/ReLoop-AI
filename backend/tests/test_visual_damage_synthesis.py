"""
Tests for Visual Damage Analysis & Condition Synthesis Pipeline.

Scenarios covered:
1. Single display observation with hairline crack -> SERVICE_REQUIRED
2. Minor display wear followed by panel crack -> evaluates ALL visual evidence, prioritizes HIGH -> SERVICE_REQUIRED
3. Panel crack followed by minor display wear -> order independence -> SERVICE_REQUIRED
4. Clean display observation -> GOOD
5. Keyboard missing key -> SERVICE_REQUIRED
6. Keyboard clean keys -> GOOD
7. Keyboard normal wear followed by missing key -> evaluates ALL, prioritizes HIGH -> SERVICE_REQUIRED
8. Keyboard missing key followed by normal wear -> order independence -> SERVICE_REQUIRED
9. Minor chassis scratch followed by severe hinge fracture -> prioritizes HIGH over LOW -> SERVICE_REQUIRED
10. Severe hinge fracture followed by minor chassis scratch -> order independence -> SERVICE_REQUIRED
11. Port damage is preserved in chas_evs and affects synthesized status (not dropped)
12. Vision routing: display_cracks route to DISPLAY, chassis_cracks route to HINGE_CHASSIS
13. Clean components get positive evidence only when inspected; uninspected components remain UNKNOWN; strict prohibition on internal hardware claims maintained.
"""
import pytest
from unittest.mock import patch
from app.db.store import store
from app.schemas.enums import EvidenceType, ComponentStatus, ComponentName
from app.schemas.evidence import EvidenceItem
from app.schemas.product import ProductRecord
from app.services.assessment_service import assessment_service
from app.services.vision import vision_service
from app.ai.gemini_client import gemini_client
from app.ai.schemas import DamageAssessmentOutput


@pytest.fixture(autouse=True)
def clean_store():
    store.clear()
    yield
    store.clear()


# ============================================================================
# Display Synthesis Scenarios
# ============================================================================

def test_display_single_crack_yields_service_required():
    """Scenario 1: Single display observation with hairline crack -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_disp_crack", manufacturer="Dell", model="Latitude 5420", model_year=2021)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="display",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Hairline crack across upper LCD panel."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    disp = profile.get_component("display")
    assert disp is not None
    assert disp.status == ComponentStatus.SERVICE_REQUIRED
    assert any("crack" in obs.lower() for obs in disp.observations)


def test_display_minor_wear_then_crack_yields_service_required():
    """Scenario 2: Minor display wear followed by panel crack -> evaluates ALL, prioritizes HIGH -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_disp_wear_then_crack", manufacturer="Apple", model="MacBook Pro 14", model_year=2021)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="display",
            value={"condition": "WEAR", "severity": "LOW", "observation": "Minor anti-reflective coating wear."},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="display",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Cracked glass panel near hinge bezel."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    disp = profile.get_component("display")
    assert disp is not None
    assert disp.status == ComponentStatus.SERVICE_REQUIRED


def test_display_crack_then_minor_wear_order_independence():
    """Scenario 3: Panel crack followed by minor wear -> order independence -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_disp_crack_then_wear", manufacturer="Apple", model="MacBook Pro 14", model_year=2021)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="display",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Cracked glass panel near hinge bezel."},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="display",
            value={"condition": "WEAR", "severity": "LOW", "observation": "Minor anti-reflective coating wear."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    disp = profile.get_component("display")
    assert disp is not None
    assert disp.status == ComponentStatus.SERVICE_REQUIRED


def test_display_clean_yields_good():
    """Scenario 4: Clean display observation -> GOOD."""
    prod = ProductRecord(id="prod_disp_clean", manufacturer="Lenovo", model="ThinkPad T14", model_year=2021)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="display",
            value={"condition": "GOOD", "severity": "NONE", "observation": "Display panel clear with no cracks or dead pixels observed."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    disp = profile.get_component("display")
    assert disp is not None
    assert disp.status == ComponentStatus.GOOD


# ============================================================================
# Keyboard Synthesis Scenarios
# ============================================================================

def test_keyboard_missing_key_yields_service_required():
    """Scenario 5: Keyboard missing key -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_kbd_missing", manufacturer="HP", model="EliteBook 840 G7", model_year=2020)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="keyboard",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Missing 'E' keycap; exposed switch mechanism."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    kbd = profile.get_component("keyboard")
    assert kbd is not None
    assert kbd.status == ComponentStatus.SERVICE_REQUIRED


def test_keyboard_clean_keys_yields_good():
    """Scenario 6: Keyboard clean keys -> GOOD."""
    prod = ProductRecord(id="prod_kbd_clean", manufacturer="HP", model="EliteBook 840 G7", model_year=2020)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="keyboard",
            value={"condition": "GOOD", "severity": "NONE", "observation": "All keycaps present, clean, and properly seated."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    kbd = profile.get_component("keyboard")
    assert kbd is not None
    assert kbd.status == ComponentStatus.GOOD


def test_keyboard_minor_wear_then_missing_key_yields_service_required():
    """Scenario 7: Normal key wear followed by missing key -> evaluates ALL, prioritizes HIGH -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_kbd_wear_then_missing", manufacturer="Dell", model="XPS 13 9310", model_year=2021)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="keyboard",
            value={"condition": "WEAR", "severity": "LOW", "observation": "Slight key shine on spacebar."},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="keyboard",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Missing 'Enter' keycap with broken scissor clip."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    kbd = profile.get_component("keyboard")
    assert kbd is not None
    assert kbd.status == ComponentStatus.SERVICE_REQUIRED


def test_keyboard_missing_key_then_minor_wear_order_independence():
    """Scenario 8: Missing key followed by normal wear -> order independence -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_kbd_missing_then_wear", manufacturer="Dell", model="XPS 13 9310", model_year=2021)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="keyboard",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Missing 'Enter' keycap with broken scissor clip."},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="keyboard",
            value={"condition": "WEAR", "severity": "LOW", "observation": "Slight key shine on spacebar."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    kbd = profile.get_component("keyboard")
    assert kbd is not None
    assert kbd.status == ComponentStatus.SERVICE_REQUIRED


# ============================================================================
# Chassis & Hinge Synthesis Scenarios
# ============================================================================

def test_chassis_minor_scratch_then_severe_hinge_fracture_yields_service_required():
    """Scenario 9: Minor chassis scratch followed by severe hinge fracture -> prioritizes HIGH -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_chas_scratch_then_hinge", manufacturer="Lenovo", model="ThinkPad X1 Carbon", model_year=2022)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="chassis",
            value={"condition": "WEAR", "severity": "LOW", "observation": "Minor cosmetic hairline scuff on bottom lid."},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="hinge",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Broken right hinge mount with casing separation."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    chas = profile.get_component("chassis")
    assert chas is not None
    assert chas.status == ComponentStatus.SERVICE_REQUIRED


def test_chassis_severe_hinge_fracture_then_scratch_order_independence():
    """Scenario 10: Severe hinge fracture followed by minor scratch -> order independence -> SERVICE_REQUIRED."""
    prod = ProductRecord(id="prod_chas_hinge_then_scratch", manufacturer="Lenovo", model="ThinkPad X1 Carbon", model_year=2022)
    store.save_product(prod)

    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="hinge",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Broken right hinge mount with casing separation."},
        ),
    )
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="chassis",
            value={"condition": "WEAR", "severity": "LOW", "observation": "Minor cosmetic hairline scuff on bottom lid."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    chas = profile.get_component("chassis")
    assert chas is not None
    assert chas.status == ComponentStatus.SERVICE_REQUIRED


def test_chassis_port_damage_preserved_and_synthesized():
    """Scenario 11: Port damage is preserved in chas_evs and affects synthesized status (not discarded)."""
    prod = ProductRecord(id="prod_chas_port_dmg", manufacturer="Dell", model="Latitude 5420", model_year=2021)
    store.save_product(prod)

    # Evidence item with component="ports" (previously discarded by assessment_service)
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical inspection",
            component="ports",
            value={"condition": "DAMAGED", "severity": "HIGH", "observation": "Left USB-C port fractured with bent contact pins."},
        ),
    )

    profile = assessment_service.build_profile(prod.id)
    chas = profile.get_component("chassis")
    assert chas is not None
    # Port damage must be evaluated into chassis/exterior condition
    assert chas.status == ComponentStatus.SERVICE_REQUIRED
    assert any("port" in obs.lower() for obs in chas.observations)


# ============================================================================
# Vision Routing & Clean Inspection Tests
# ============================================================================

def test_vision_routing_display_vs_chassis_cracks():
    """Scenario 12: display_cracks route to DISPLAY; chassis_cracks route to HINGE_CHASSIS."""
    prod = ProductRecord(id="prod_routing_test", manufacturer="HP", model="Spectre x360", model_year=2022)
    store.save_product(prod)

    mock_ai_output = DamageAssessmentOutput(
        display_cracks=["Hairline diagonal crack on display glass."],
        chassis_cracks=["Cracked bottom left corner casing."],
        dents=[],
        missing_keys=[],
        hinge_damage=[],
        port_damage=[],
        visible_swelling=[],
        observations=[],
        components_inspected_clean=[],
        components_not_assessable=[],
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        res = vision_service.analyze(
            product_id=prod.id,
            image_bytes_list=[b"\xff\xd8\xff" + b"fakejpegdata" * 10],
            inspection_notes="",
        )

    # Check findings routing
    display_findings = [f for f in res.findings if "display" in str(f.component).lower()]
    chassis_findings = [f for f in res.findings if "hinge" in str(f.component).lower() or "chassis" in str(f.component).lower()]

    assert len(display_findings) >= 1
    assert any("display glass" in f.description.lower() for f in display_findings)

    assert len(chassis_findings) >= 1
    assert any("bottom left corner" in f.description.lower() for f in chassis_findings)


def test_vision_clean_components_and_uninspected_unknown():
    """
    Scenario 13:
    Only components in components_inspected_clean receive positive evidence.
    Components not inspected do NOT receive fake evidence.
    Strict prohibition on internal hardware claims maintained.
    """
    prod = ProductRecord(id="prod_clean_test", manufacturer="Lenovo", model="ThinkPad T14", model_year=2021)
    store.save_product(prod)

    # User uploaded only screen photo: display is inspected clean, keyboard/chassis/ports were not inspected
    mock_ai_output = DamageAssessmentOutput(
        display_cracks=[],
        chassis_cracks=[],
        dents=[],
        missing_keys=[],
        hinge_damage=[],
        port_damage=[],
        visible_swelling=[],
        observations=[],
        components_inspected_clean=["display"],
        components_not_assessable=["keyboard", "chassis", "ports"],
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        res = vision_service.analyze(
            product_id=prod.id,
            image_bytes_list=[b"\xff\xd8\xff" + b"fakejpegdata" * 10],
            inspection_notes="",
        )

    # Display should have a clean finding
    display_findings = [f for f in res.findings if "display" in str(f.component).lower()]
    assert len(display_findings) == 1
    assert display_findings[0].severity == "NONE"

    # Keyboard should NOT have positive evidence
    kbd_findings = [f for f in res.findings if "keyboard" in str(f.component).lower()]
    assert len(kbd_findings) == 0

    # Internal components (battery, ssd, ram) must have ZERO findings
    internal_findings = [f for f in res.findings if any(k in str(f.component).lower() for k in ["battery", "ssd", "ram", "thermals", "system"])]
    assert len(internal_findings) == 0

    # Build profile: display is GOOD; keyboard and internal components remain UNKNOWN
    profile = assessment_service.build_profile(prod.id)
    assert profile.get_component("display").status == ComponentStatus.GOOD
    assert profile.get_component("keyboard").status == ComponentStatus.UNKNOWN
    assert profile.get_component("battery").status == ComponentStatus.UNKNOWN
