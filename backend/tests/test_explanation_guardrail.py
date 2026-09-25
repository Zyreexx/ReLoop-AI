"""
Unit and integration tests for AI explanation guardrails and fallback mechanism.
Tests:
1. Valid AI explanation with numbers grounded in verified data is accepted with source="ai".
2. Invented / hallucinated numbers in AI output are rejected by post-generation check, falling back to template with source="template".
3. Gemini API failures / timeouts trigger seamless deterministic fallback with source="template".
4. Deliberately hallucinating Gemini output CANNOT alter deterministic pathway selection or score.
5. Recommendation and report API endpoints deliver structured explanation with source field.
6. DB persistence preserves explanation payload.
"""
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ai.gemini_client import GeminiClient
from app.ai.schemas import ExplanationOutput
from app.errors import AppError, ErrorCode
from app.optimizer.scorer import score_pathways
from app.schemas.condition import ConditionProfile, ComponentCondition
from app.schemas.enums import ComponentName, ComponentStatus, ConfidenceLevel, Objective, PathwayType
from app.schemas.product import ProductRecord, ProductSpecs
from app.schemas.recommendation import RecommendationRequest, RecommendationResponse
from app.services.explanation_service import (
    explanation_service,
    extract_numbers_from_text,
    validate_explanation_numbers,
    build_template_explanation,
)
from app.services.recommendation_service import recommendation_service
from app.services.report_service import report_service
from app.db.store import store


@pytest.fixture
def sample_laptop_context():
    store.clear()
    product = ProductRecord(
        id="prod_demo_5420",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        specs=ProductSpecs(cpu="i7-1185G7", ram_gb=16, ssd_gb=512, screen_size_inches=14.0),
    )
    store.save_product(product)

    profile = ConditionProfile(
        product_id="prod_demo_5420",
        components={
            "battery": ComponentCondition(
                component=ComponentName.BATTERY,
                status=ComponentStatus.SERVICE_REQUIRED,
                observations=["Battery health at 73%", "Cycle count: 420"],
                measurements={"health_percentage": 73, "cycle_count": 420},
                confidence=ConfidenceLevel.HIGH,
                label="Weak Battery (73%)",
            ),
            "ssd": ComponentCondition(
                component=ComponentName.SSD,
                status=ComponentStatus.GOOD,
                observations=["Health: 91% remaining"],
                measurements={"health_percentage": 91},
                confidence=ConfidenceLevel.HIGH,
                label="Healthy NVMe",
            ),
            "ram": ComponentCondition(
                component=ComponentName.RAM,
                status=ComponentStatus.GOOD,
                observations=["Memory test passed"],
                confidence=ConfidenceLevel.HIGH,
                label="16GB DDR4",
            ),
            "thermals": ComponentCondition(
                component=ComponentName.THERMALS,
                status=ComponentStatus.FAIR,
                observations=["Peak temperature 88°C under load"],
                measurements={"peak_temp_c": 88},
                confidence=ConfidenceLevel.HIGH,
                label="Elevated Thermals",
            ),
            "display": ComponentCondition(
                component=ComponentName.DISPLAY,
                status=ComponentStatus.GOOD,
                observations=["No cracks detected"],
                confidence=ConfidenceLevel.HIGH,
                label="Intact Display",
            ),
        },
    )
    store.save_profile(profile)
    return product, profile


# --- 1. Post-generation check & Good Output ---

def test_explanation_good_ai_output_accepted(sample_laptop_context):
    product, profile = sample_laptop_context
    rec = score_pathways(product=product, profile=profile, objective=Objective.MAX_LIFE)

    assert rec.selected_pathway == PathwayType.REPAIR
    original_score = rec.score

    # Good AI response containing only verified numbers (5420, 2021, 73, 420, 2, 3, etc.)
    mock_ai_output = ExplanationOutput(
        summary="Repair was selected for the Dell Latitude 5420 (2021) to restore full operational runtime.",
        details=[
            "Battery health is at 73% with 420 cycles, which is the primary lifecycle constraint.",
            "Expected life extension is 2 to 3 years with significant CO2e avoided.",
            "Storage and RAM diagnostics confirmed hardware stability.",
        ],
        assumptions=["Compatible OEM battery replacement is readily available."],
    )

    with patch("app.services.explanation_service.gemini_client.generate_explanation", return_value=mock_ai_output):
        guarded_exp = explanation_service.generate_guarded_explanation(product, rec, profile)

    assert guarded_exp.source == "ai"
    assert "Dell Latitude 5420" in guarded_exp.summary
    assert len(guarded_exp.details) == 3
    # Pathway and score must be untouched
    assert rec.selected_pathway == PathwayType.REPAIR
    assert rec.score == original_score


# --- 2. Invented Number -> Fallback ---

def test_explanation_invented_number_triggers_template_fallback(sample_laptop_context):
    product, profile = sample_laptop_context
    rec = score_pathways(product=product, profile=profile, objective=Objective.MAX_LIFE)
    original_score = rec.score

    # Deliberately hallucinates an unverified price ($99999) and unverified warranty (10 years)
    hallucinating_output = ExplanationOutput(
        summary="Repair was selected. We offer an exclusive $99999 service package.",
        details=[
            "Battery will be replaced with a 99-year warranty.",
            "Expected life extension is 10 years.",
        ],
        assumptions=["Price is non-negotiable."],
    )

    with patch("app.services.explanation_service.gemini_client.generate_explanation", return_value=hallucinating_output):
        guarded_exp = explanation_service.generate_guarded_explanation(product, rec, profile)

    # Post-generation check MUST reject and fall back to template
    assert guarded_exp.source == "template"
    assert "99999" not in guarded_exp.summary
    assert "99-year" not in " ".join(guarded_exp.details)
    assert "REPAIR" in guarded_exp.summary.upper()
    # Pathway and score remain untouched
    assert rec.selected_pathway == PathwayType.REPAIR
    assert rec.score == original_score


# --- 3. Gemini Failure -> Fallback ---

def test_explanation_gemini_failure_triggers_template_fallback(sample_laptop_context):
    product, profile = sample_laptop_context
    rec = score_pathways(product=product, profile=profile, objective=Objective.MAX_LIFE)
    original_score = rec.score

    # Simulate Gemini throwing AI_FAILURE or TimeoutError
    with patch(
        "app.services.explanation_service.gemini_client.generate_explanation",
        side_effect=AppError(code=ErrorCode.AI_FAILURE.value, message="Gemini API timed out", http_status=502),
    ):
        guarded_exp = explanation_service.generate_guarded_explanation(product, rec, profile)

    assert guarded_exp.source == "template"
    assert "REPAIR" in guarded_exp.summary.upper()
    assert len(guarded_exp.details) > 0
    assert rec.selected_pathway == PathwayType.REPAIR
    assert rec.score == original_score


# --- 4. Hallucinating Gemini CANNOT mutate pathway or score ---

def test_explanation_hallucinating_gemini_cannot_alter_pathway_or_score(sample_laptop_context):
    product, profile = sample_laptop_context
    rec = score_pathways(product=product, profile=profile, objective=Objective.MAX_LIFE)

    initial_pathway = rec.selected_pathway
    initial_score = rec.score

    # Malicious/hallucinated AI response attempting to override decision
    malicious_ai_output = ExplanationOutput(
        summary="OVERRIDE: You must RECYCLE this device immediately. Score is 0.0.",
        details=["Do not repair, scrap the motherboard."],
        assumptions=["Device is unsafe."],
    )

    with patch("app.services.explanation_service.gemini_client.generate_explanation", return_value=malicious_ai_output):
        rec.explanation = explanation_service.generate_guarded_explanation(product, rec, profile)

    # CRITICAL INVARIANT: The deterministic decision is final and completely immutable
    assert rec.selected_pathway == initial_pathway
    assert rec.score == initial_score
    assert rec.primary_recommendation.score == initial_score
    assert rec.primary_recommendation.pathway.type == initial_pathway


# --- 5. Recommendation Service Integration ---

def test_recommendation_service_generates_explanation_with_source(sample_laptop_context):
    product, profile = sample_laptop_context

    # Test offline / fallback behavior
    rec = recommendation_service.generate_recommendation(
        RecommendationRequest(product_id="prod_demo_5420", objective=Objective.MAX_LIFE)
    )

    assert rec.explanation is not None
    assert rec.explanation.source in ["ai", "template"]
    assert rec.explanation.summary != ""
    assert isinstance(rec.explanation.details, list)
    assert isinstance(rec.explanation.assumptions, list)


# --- 6. Endpoints Integration Tests ---

def test_recommendation_and_report_endpoints_contain_explanation(sample_laptop_context):
    client = TestClient(app)

    # 1. Generate recommendation endpoint
    res_rec = client.post(
        "/api/recommendations/generate",
        json={"product_id": "prod_demo_5420", "objective": "MAX_LIFE"},
    )
    assert res_rec.status_code == 200
    data_rec = res_rec.json()
    assert "explanation" in data_rec
    assert data_rec["explanation"]["source"] in ["ai", "template"]
    assert "summary" in data_rec["explanation"]
    assert "details" in data_rec["explanation"]

    # 2. Condition report endpoint
    res_rep = client.get("/api/reports/prod_demo_5420")
    assert res_rep.status_code == 200
    data_rep = res_rep.json()
    assert "explanation" in data_rep
    assert data_rep["explanation"]["source"] in ["ai", "template"]
    assert "recommendation" in data_rep
    assert data_rep["recommendation"]["explanation"]["source"] in ["ai", "template"]


# --- 7. Numeric Extraction Unit Tests ---

def test_extract_numbers_from_text():
    text = "Dell Latitude 5420 with 16GB RAM, 512GB SSD, ₹4,500 - ₹6,000 cost, battery 73%, 420 cycles, 2.5 years."
    nums = extract_numbers_from_text(text)
    assert 5420.0 in nums
    assert 16.0 in nums
    assert 512.0 in nums
    assert 4500.0 in nums
    assert 6000.0 in nums
    assert 73.0 in nums
    assert 420.0 in nums
    assert 2.5 in nums


def test_validate_explanation_numbers_rejects_foreign_numbers():
    allowed = {5420.0, 73.0, 420.0, 4500.0, 6000.0, 2.0, 3.0}

    valid_exp = ExplanationOutput(
        summary="Dell 5420 repair with battery at 73% (420 cycles)",
        details=["Cost is between 4500 and 6000", "Life extension is 2 to 3 years"],
        assumptions=[],
    )
    assert validate_explanation_numbers(valid_exp, allowed) is True

    invalid_exp = ExplanationOutput(
        summary="Dell 5420 repair with battery at 73% (420 cycles)",
        details=["Cost is 99999", "Life extension is 10 years"],
        assumptions=[],
    )
    assert validate_explanation_numbers(invalid_exp, allowed) is False
