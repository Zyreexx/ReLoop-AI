"""
Unit and integration tests for:
- Catalog matching with fuzzy alias normalization
- Generic laptop category fallback profile
- Precision gating in assessment, recommendations, and condition reports (is_generic_assessment flag)
- Generic estimate basis transparency (GENERIC_CATEGORY_ESTIMATE)
- Three-way options in failure/unknown path
"""
from io import BytesIO
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from app.ai.gemini_client import gemini_client
from app.ai.schemas import OpenIdentificationOutput
from app.db.store import store
from app.knowledge.loader import (
    match_catalog_model,
    get_generic_laptop_profile,
    get_model_spec_or_generic,
    get_repair_cost_with_fallback,
    get_useful_life_with_fallback,
    load_all_products,
)
from app.schemas.enums import Objective, ComponentStatus, ConfidenceLevel
from app.schemas.evidence import EvidenceItem, EvidenceType
from app.schemas.product import ProductCreate, ProductRecord, ProductSpecs
from app.services.assessment_service import assessment_service
from app.services.product_service import product_service
from app.services.recommendation_service import recommendation_service
from app.services.report_service import report_service

VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 30


# ============================================================================
# 1. Knowledge Matching & Aliases Tests
# ============================================================================

def test_match_catalog_model_exact_and_aliases():
    """Identified model matches an existing catalog entry via exact name or alias."""
    # Dell Latitude 5420
    match_dell_exact = match_catalog_model("Dell", "Latitude 5420")
    assert match_dell_exact is not None
    assert match_dell_exact["slug"] == "dell-latitude-5420"

    match_dell_alias = match_catalog_model("Dell", "5420")
    assert match_dell_alias is not None
    assert match_dell_alias["slug"] == "dell-latitude-5420"

    # Apple MacBook Air
    match_apple = match_catalog_model("Apple", "MacBook Air M1")
    assert match_apple is not None
    assert match_apple["slug"] == "apple-macbook-air-m1-2020"

    # HP EliteBook 840 G7
    match_hp = match_catalog_model("HP", "840 G7")
    assert match_hp is not None
    assert match_hp["slug"] == "hp-elitebook-840-g7"

    # Lenovo ThinkPad T14 Gen 1
    match_lenovo = match_catalog_model("Lenovo", "ThinkPad T14")
    assert match_lenovo is not None
    assert match_lenovo["slug"] == "lenovo-thinkpad-t14-gen-1"


def test_match_catalog_model_non_catalog_returns_none_without_guessing():
    """Models not in our 4-entry catalog must return None, not guess a closest match."""
    assert match_catalog_model("Acer", "Aspire 5") is None
    assert match_catalog_model("ASUS", "ZenBook 14 UX425") is None
    assert match_catalog_model("Dell", "XPS 15 9500") is None
    assert match_catalog_model("Lenovo", "Legion 5") is None
    assert match_catalog_model("Unknown", "Laptop") is None
    assert match_catalog_model(None, None) is None


def test_generic_laptop_profile_loads_with_generic_basis():
    """Generic category profile provides broad category estimates with GENERIC_CATEGORY_ESTIMATE basis."""
    generic = get_generic_laptop_profile()
    assert generic["manufacturer"] == "Generic"
    assert generic["is_generic"] is True
    assert generic["specs"]["category"] == "LAPTOP"

    # Check repair costs have GENERIC_CATEGORY_ESTIMATE basis
    repair_costs = generic["typical_repair_cost_inr"]
    assert "battery" in repair_costs
    assert repair_costs["battery"]["basis"] == "GENERIC_CATEGORY_ESTIMATE"
    assert repair_costs["ssd"]["basis"] == "GENERIC_CATEGORY_ESTIMATE"

    # Check useful life has GENERIC_CATEGORY_ESTIMATE basis
    useful_life = generic["expected_useful_life"]
    assert useful_life["basis"] == "GENERIC_CATEGORY_ESTIMATE"


def test_load_all_products_excludes_generic_profile():
    """load_all_products only contains the specific curated catalog models, not _generic_laptop."""
    prods = load_all_products()
    assert "generic-laptop" not in prods
    assert all(not slug.startswith("_") for slug in prods)
    assert len(prods) == 4


# ============================================================================
# 2. Precision Gating in Assessment, Recommendation, and Report
# ============================================================================

def test_catalog_matched_model_uses_precise_data_is_generic_false():
    """When a device matches catalog, is_generic_assessment is False and precise data is used."""
    prod = product_service.create_or_confirm(
        ProductCreate(
            manufacturer="Dell",
            model="Latitude 5420",
            model_year=2021,
            age_years=4.0,
        )
    )
    assert prod.is_generic is False
    assert prod.is_generic_assessment is False

    # Add sample diagnostic evidence
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.DIAGNOSTIC,
            source="OEM Diagnostics",
            component="battery",
            value={"health_percentage": 88.0, "cycle_count": 310},
            confidence=ConfidenceLevel.HIGH,
        ),
    )

    # 1. Build profile
    profile = assessment_service.build_profile(prod.id)
    assert profile.is_generic_assessment is False

    # 2. Generate recommendation
    from app.schemas.recommendation import RecommendationRequest
    rec = recommendation_service.generate_recommendation(
        RecommendationRequest(product_id=prod.id, objective=Objective.MAX_LIFE)
    )
    assert rec.is_generic_assessment is False

    # 3. Generate report
    rep = report_service.get_report(profile.product_id)
    assert rep.is_generic_assessment is False


def test_uncataloged_model_uses_generic_estimate_is_generic_true():
    """When a device is not in catalog (e.g. Acer Aspire 5), is_generic_assessment is True and basis is GENERIC_CATEGORY_ESTIMATE."""
    prod = product_service.create_or_confirm(
        ProductCreate(
            manufacturer="Acer",
            model="Aspire 5 A515-56",
            model_year=2021,
            age_years=4.0,
        )
    )
    assert prod.is_generic is True
    assert prod.is_generic_assessment is True

    # Add visual evidence
    store.add_evidence(
        prod.id,
        EvidenceItem(
            type=EvidenceType.VISUAL,
            source="Optical Inspection",
            component="display",
            value={"visible_status": "GOOD", "observation": "Screen clean"},
            confidence=ConfidenceLevel.HIGH,
        ),
    )

    # 1. Build profile
    profile = assessment_service.build_profile(prod.id)
    assert profile.is_generic_assessment is True

    # 2. Generate recommendation
    from app.schemas.recommendation import RecommendationRequest
    rec = recommendation_service.generate_recommendation(
        RecommendationRequest(product_id=prod.id, objective=Objective.MAX_LIFE)
    )
    assert rec.is_generic_assessment is True
    assert any("Broad category estimates" in a for a in rec.assumptions)

    # Every pathway estimate carries basis="GENERIC_CATEGORY_ESTIMATE"
    if rec.primary_recommendation and rec.primary_recommendation.pathway:
        primary_pw = rec.primary_recommendation.pathway
        assert primary_pw.estimated_cost.basis == "GENERIC_CATEGORY_ESTIMATE"
        assert primary_pw.expected_life_extension.basis == "GENERIC_CATEGORY_ESTIMATE"
        assert primary_pw.environmental_estimate.basis == "GENERIC_CATEGORY_ESTIMATE"

    for alt in rec.alternative_pathways:
        pw = getattr(alt, "pathway", alt)
        if pw:
            assert pw.estimated_cost.basis == "GENERIC_CATEGORY_ESTIMATE"
            assert pw.expected_life_extension.basis == "GENERIC_CATEGORY_ESTIMATE"

    # 3. Generate report
    rep = report_service.get_report(profile.product_id)
    assert rep.is_generic_assessment is True
    assert any("General laptop category estimate applied" in a for a in rep.assumptions)


# ============================================================================
# 3. Three-Way Fallback Offering on Failure Path
# ============================================================================

def test_identify_unknown_offers_three_options(client: TestClient):
    """When identification returns UNKNOWN, response provides supported catalog models and generic fallback."""
    mock_ai_output = OpenIdentificationOutput(
        manufacturer="UNKNOWN",
        model="UNKNOWN",
        label_evidence=[],
        visual_evidence=["Unclear dark chassis"],
        contradictions=[],
        model_confidence=0.2,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("blurry.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UNKNOWN"
    assert data["is_supported"] is False

    # Option 1: Pick from known catalog
    assert len(data["supported_models"]) >= 4

    # Option 2: Continue with general laptop assessment
    assert data["generic_fallback_available"] is True
    assert data["generic_model"] is not None
    assert data["generic_model"]["manufacturer"] == "Generic"
    assert data["generic_model"]["model"] == "General Laptop"


def test_identify_ai_unavailable_offers_three_options(client: TestClient, monkeypatch):
    """When AI is unavailable, response provides supported models and generic fallback option."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
    with patch.object(gemini_client, "generate_structured", side_effect=Exception("API Connection Timeout")):
        files = [("images", ("laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AI_UNAVAILABLE"
    assert data["generic_fallback_available"] is True
    assert data["generic_model"] is not None
    assert len(data["supported_models"]) >= 4


def test_manual_generic_laptop_selection(client: TestClient):
    """Client can manually select the general laptop profile and get a valid response."""
    res = client.post("/api/products/identify", json={"manual_model": "generic-laptop"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IDENTIFIED"
    assert data["identified_model"]["manufacturer"] == "Generic"
    assert data["identified_model"]["model"] == "General Laptop"
    assert data["is_supported"] is False
