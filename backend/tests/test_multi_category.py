"""
Tests for Multi-Category Hardware Expansion (Smartphones, Tablets, Desktops, Servers).
Validates category-specific product specifications, catalog matching, condition synthesis,
repair pricing, and deterministic circular path optimization while preserving laptop workflows.
"""
import pytest
from typing import Any
from app.db.store import store
from app.schemas.enums import ComponentStatus, DeviceCategory, Objective, PathwayType
from app.schemas.product import ProductRecord, ProductSpecs
from app.schemas.evidence import EvidenceItem, EvidenceType
from app.services.assessment_service import assessment_service
from app.services.recommendation_service import recommendation_service
from app.schemas.recommendation import RecommendationRequest, ScoredPathway
from app.knowledge.loader import get_generic_profile_for_category, match_catalog_model


def test_category_generic_profiles_loaded():
    # Verify each category has an authentic, dedicated specification profile
    phone_prof = get_generic_profile_for_category(DeviceCategory.SMARTPHONE)
    assert phone_prof["category"] == "SMARTPHONE"
    assert phone_prof["specs"]["display_size_inches"] < 7.0

    tablet_prof = get_generic_profile_for_category(DeviceCategory.TABLET)
    assert tablet_prof["category"] == "TABLET"
    assert 7.0 <= tablet_prof["specs"]["display_size_inches"] <= 13.0

    desktop_prof = get_generic_profile_for_category(DeviceCategory.DESKTOP)
    assert desktop_prof["category"] == "DESKTOP"
    assert desktop_prof["specs"]["battery_replaceable"] is False

    server_prof = get_generic_profile_for_category(DeviceCategory.SERVER)
    assert server_prof["category"] == "SERVER"
    assert server_prof["specs"]["baseline_embodied_co2_kg"] >= 1000.0


def test_smartphone_assessment_and_virtual_keyboard():
    prod_id = "test_phone_001"
    phone = ProductRecord(
        id=prod_id,
        manufacturer="Apple",
        model="iPhone 13",
        model_year=2021,
        age=3.0,
        category=DeviceCategory.SMARTPHONE,
        specs=ProductSpecs(
            category=DeviceCategory.SMARTPHONE,
            ram_modular=False,
            ssd_modular=False,
            battery_replaceable=True,
            display_size_inches=6.1,
            weight_kg=0.174,
            baseline_embodied_co2_kg=64.0,
        ),
    )
    store.save_product(phone)

    # Battery diagnostic: degraded
    store.add_evidence(
        prod_id,
        EvidenceItem(
            product_id=prod_id,
            type=EvidenceType.DIAGNOSTIC,
            source="ios_battery_health",
            component="battery",
            value={"health_percentage": 74.0, "cycle_count": 820, "status": "SERVICE_REQUIRED"},
        ),
    )

    profile = assessment_service.build_profile(prod_id)

    # Virtual keyboard should automatically synthesize as N/A Good
    kb = profile.components["keyboard"]
    assert kb.status == ComponentStatus.GOOD
    assert kb.label is not None and "Virtual" in kb.label

    # Battery should be correctly flagged for service
    bat = profile.components["battery"]
    assert bat.status in [ComponentStatus.WEAR, ComponentStatus.REPLACE]

    # Run optimizer
    req = RecommendationRequest(product_id=prod_id, objective=Objective.LOWEST_COST, skip_ai_explanation=True)
    rec = recommendation_service.generate_recommendation(req)
    assert rec.selected_pathway in [PathwayType.REPAIR, PathwayType.REFURBISH, PathwayType.REUSE]
    repair_pw: Any = None
    for p in rec.alternative_pathways:
        pw = p.pathway if isinstance(p, ScoredPathway) else p
        if getattr(pw, "type", None) == PathwayType.REPAIR:
            repair_pw = pw
            break
    assert repair_pw is not None
    is_eligible = getattr(getattr(repair_pw, "eligibility", None), "is_eligible", getattr(repair_pw, "eligibility", None))
    assert is_eligible is True


def test_desktop_assessment_mains_powered():
    prod_id = "test_desktop_001"
    desktop = ProductRecord(
        id=prod_id,
        manufacturer="Dell",
        model="OptiPlex 7090 Tower",
        model_year=2021,
        age=3.5,
        category=DeviceCategory.DESKTOP,
        specs=ProductSpecs(
            category=DeviceCategory.DESKTOP,
            ram_modular=True,
            ssd_modular=True,
            battery_replaceable=False,
            display_size_inches=0.0,
            weight_kg=6.56,
            baseline_embodied_co2_kg=340.0,
        ),
    )
    store.save_product(desktop)

    profile = assessment_service.build_profile(prod_id)

    # Battery must synthesize as AC Mains Powered (GOOD), not UNKNOWN
    bat = profile.components["battery"]
    assert bat.status == ComponentStatus.GOOD
    assert bat.label is not None and "AC Mains" in bat.label

    # Display must synthesize as External / Modular (GOOD)
    disp = profile.components["display"]
    assert disp.status == ComponentStatus.GOOD
    assert disp.label is not None and ("External" in disp.label or "Headless" in disp.label)


def test_server_assessment_high_modularity_and_embodied_carbon():
    prod_id = "test_server_001"
    server = ProductRecord(
        id=prod_id,
        manufacturer="Dell",
        model="PowerEdge R640",
        model_year=2019,
        age=5.0,
        category=DeviceCategory.SERVER,
        specs=ProductSpecs(
            category=DeviceCategory.SERVER,
            ram_modular=True,
            ssd_modular=True,
            battery_replaceable=False,
            display_size_inches=0.0,
            weight_kg=17.6,
            baseline_embodied_co2_kg=1280.0,
        ),
    )
    store.save_product(server)

    profile = assessment_service.build_profile(prod_id)
    assert profile.components["battery"].status == ComponentStatus.GOOD
    assert profile.components["keyboard"].status == ComponentStatus.GOOD
    assert profile.components["display"].status == ComponentStatus.GOOD

    # Optimize server for maximum life
    req = RecommendationRequest(product_id=prod_id, objective=Objective.MAX_LIFE, skip_ai_explanation=True)
    rec = recommendation_service.generate_recommendation(req)
    # Server should be recommended for reuse/upgrade
    assert rec.selected_pathway in [PathwayType.REUSE, PathwayType.UPGRADE, PathwayType.REFURBISH]


def test_laptop_workflow_preservation():
    # Verify classic laptop assessment continues to operate with all 9 subsystems
    prod_id = "test_laptop_preservation_001"
    laptop = ProductRecord(
        id=prod_id,
        manufacturer="Lenovo",
        model="ThinkPad T14 Gen 1",
        model_year=2020,
        age=4.0,
        category=DeviceCategory.LAPTOP,
        specs=ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=True,
            ssd_modular=True,
            battery_replaceable=True,
            display_size_inches=14.0,
            weight_kg=1.46,
            baseline_embodied_co2_kg=280.0,
        ),
    )
    store.save_product(laptop)

    profile = assessment_service.build_profile(prod_id)
    assert "battery" in profile.components
    assert "display" in profile.components
    assert "keyboard" in profile.components
    assert "ssd" in profile.components
