"""
Tests for shared contracts, Pydantic v2 schemas, and global error handling.
Validates:
1. Enums: EvidenceType, ComponentName, ComponentStatus, PathwayType, Objective
2. Architecture section 6 models: Product, Evidence, ComponentCondition, Pathway, Recommendation
3. Reusable Estimate model
4. Request/response models for all section 9 endpoints
5. Diagnostic validations: battery, ssd, ram, thermals, system
6. AppError and global error handler behavior (rules.md format + INTERNAL_ERROR on unhandled)
"""
from datetime import datetime
import pytest
from pydantic import ValidationError
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.schemas.enums import (
    EvidenceType,
    ComponentName,
    ComponentStatus,
    PathwayType,
    Objective,
)
from app.schemas.estimate import Estimate
from app.schemas.product import (
    Product,
    ProductIdentifyRequest,
    ProductIdentifyResponse,
    ProductCandidate,
    ProductSpecs,
)
from app.schemas.evidence import Evidence
from app.schemas.condition import (
    ComponentCondition,
    AssessmentBuildRequest,
    AssessmentBuildResponse,
)
from app.schemas.pathway import (
    Pathway,
    PathwayEligibility,
    EnvironmentalEstimate,
    LogisticsEstimate,
)
from app.schemas.recommendation import (
    Recommendation,
    RecommendationsGenerateRequest,
    RecommendationsGenerateResponse,
    ScoredPathway,
)
from app.schemas.diagnostics import (
    BatteryDiagnostic,
    SsdDiagnostic,
    RamDiagnostic,
    ThermalDiagnostic,
    SystemDiagnostic,
    DiagnosticsValidateRequest,
    DiagnosticsValidateResponse,
)
from app.schemas.symptoms import (
    SymptomsParseRequest,
    SymptomsParseResponse,
)
from app.schemas.vision import (
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
)
from app.errors import (
    AppError,
    ErrorCode,
    register_error_handlers,
    INVALID_INPUT,
    UNSUPPORTED_MODEL,
    INVALID_DIAGNOSTIC,
    AI_FAILURE,
    MISSING_EVIDENCE,
    INVALID_PATHWAY_CALC,
    NOT_FOUND,
    INTERNAL_ERROR,
)


# --- 1. Enums Verification ---

def test_enums_members():
    # EvidenceType
    assert set(EvidenceType) == {
        EvidenceType.VISUAL,
        EvidenceType.DIAGNOSTIC,
        EvidenceType.USER_REPORTED,
        EvidenceType.DATABASE,
        EvidenceType.ESTIMATE,
    }

    # ComponentName
    assert set(ComponentName) == {
        ComponentName.BATTERY,
        ComponentName.SSD,
        ComponentName.RAM,
        ComponentName.THERMALS,
        ComponentName.DISPLAY,
        ComponentName.KEYBOARD,
        ComponentName.HINGE_CHASSIS,
        ComponentName.SYSTEM,
    }

    # ComponentStatus
    assert ComponentStatus.GOOD == "GOOD"
    assert ComponentStatus.WEAR == "WEAR"
    assert ComponentStatus.REPLACE == "REPLACE"
    assert ComponentStatus.DAMAGED == "DAMAGED"
    assert ComponentStatus.UNKNOWN == "UNKNOWN"

    # PathwayType
    assert set(PathwayType) == {
        PathwayType.REPAIR,
        PathwayType.UPGRADE,
        PathwayType.REFURBISH,
        PathwayType.REUSE,
        PathwayType.COMPONENT_RECOVERY,
        PathwayType.RECYCLE,
    }

    # Objective
    assert set(Objective) == {
        Objective.LOWEST_COST,
        Objective.MAX_LIFE,
        Objective.ENVIRONMENTAL,
        Objective.FASTEST_RECOVERY,
    }


# --- 2. Reusable Estimate Model ---

def test_estimate_model():
    est = Estimate(
        value_min=45.0,
        value_max=75.0,
        unit="USD",
        basis="DATABASE",
        assumptions=["Standard market part price", "Local distribution stock"],
    )
    assert est.value_min == 45.0
    assert est.value_max == 75.0
    assert est.unit == "USD"
    assert est.basis == "DATABASE"
    assert len(est.assumptions) == 2
    assert est.display_range == "$45–$75"


# --- 3. Architecture Section 6 Models ---

def test_product_model():
    p = Product(
        id="prod_test123",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        category="LAPTOP",
        serial_or_identifier="SN12345",
        age=4.5,
    )
    assert p.id == "prod_test123"
    assert p.manufacturer == "Dell"
    assert p.model == "Latitude 5420"
    assert p.model_year == 2021
    assert p.category == "LAPTOP"
    assert p.serial_or_identifier == "SN12345"
    assert p.age == 4.5
    assert p.age_years == 4.5


def test_evidence_model():
    ev = Evidence(
        id="ev_001",
        product_id="prod_test123",
        type=EvidenceType.DIAGNOSTIC,
        source="Battery Health Diagnostic",
        value={"health_percent": 73.0, "cycle_count": 584},
        confidence="HIGH",
    )
    assert ev.id == "ev_001"
    assert ev.product_id == "prod_test123"
    assert ev.type == EvidenceType.DIAGNOSTIC
    assert ev.source == "Battery Health Diagnostic"
    assert ev.value["health_percent"] == 73.0
    assert isinstance(ev.timestamp, datetime)


def test_component_condition_model():
    cond = ComponentCondition(
        component=ComponentName.BATTERY,
        status=ComponentStatus.WEAR,
        observations=["Measured 42,340 mWh full charge of 58,000 mWh design."],
        measurements={"health_percent": 73.0, "cycle_count": 584},
        confidence="HIGH",
        evidence_ids=["ev_001"],
    )
    assert cond.component == ComponentName.BATTERY
    assert cond.status == ComponentStatus.WEAR
    assert len(cond.observations) == 1
    assert cond.measurements["health_percent"] == 73.0
    assert cond.evidence_ids == ["ev_001"]


def test_pathway_model():
    pathway = Pathway(
        type=PathwayType.REPAIR,
        eligibility=PathwayEligibility(is_eligible=True, reasons=["Battery degraded"]),
        estimated_cost=Estimate(
            value_min=45.0,
            value_max=75.0,
            unit="USD",
            basis="DATABASE",
            assumptions=["OEM compatible"],
        ),
        expected_life_extension=Estimate(
            value_min=2.5,
            value_max=4.0,
            unit="years",
            basis="MODEL_ESTIMATE",
            assumptions=["Proper charge habits"],
        ),
        value_retained=92.0,
        material_retained=96.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=210.0,
            co2_avoided_kg_max=275.0,
            ewaste_diverted_kg=1.35,
        ),
        logistics=LogisticsEstimate(
            complexity="LOW",
            turnaround_days_min=1,
            turnaround_days_max=3,
        ),
        assumptions=["Data retained"],
    )
    assert pathway.type == PathwayType.REPAIR
    assert pathway.value_retained == 92.0
    assert pathway.material_retained == 96.0
    assert pathway.estimated_cost.value_min == 45.0


def test_recommendation_model():
    rec = Recommendation(
        selected_pathway=PathwayType.REPAIR,
        objective=Objective.MAX_LIFE,
        score=88.5,
        alternative_pathways=[],
        reasoning=["Battery degraded to 73%", "SSD remains healthy"],
        evidence_ids=["ev_001", "ev_002"],
        assumptions=["Parts available"],
    )
    assert rec.selected_pathway == PathwayType.REPAIR
    assert rec.objective == Objective.MAX_LIFE
    assert rec.score == 88.5
    assert len(rec.reasoning) == 2
    assert len(rec.evidence_ids) == 2


# --- 4. Section 9 Endpoint Contracts & Diagnostics Inputs ---

def test_diagnostics_validation_contract():
    # Covers: battery (design_capacity, full_charge_capacity, cycle_count),
    # ssd (health_percent), ram (test_result PASS/FAIL), thermals (max_temp_c, throttling_detected),
    # system (critical_errors list)
    req = DiagnosticsValidateRequest(
        product_id="prod_test1",
        battery=BatteryDiagnostic(
            design_capacity=58000.0,
            full_charge_capacity=42340.0,
            cycle_count=584,
        ),
        ssd=SsdDiagnostic(
            health_percent=91.0,
            smart_status="PASS",
        ),
        ram=RamDiagnostic(
            test_result="PASS",
            installed_gb=16,
        ),
        thermals=ThermalDiagnostic(
            max_temp_c=96.0,
            throttling_detected=True,
        ),
        system=SystemDiagnostic(
            critical_errors=[],
            post_successful=True,
        ),
    )
    assert req.battery.design_capacity == 58000.0
    assert req.battery.full_charge_capacity == 42340.0
    assert req.battery.cycle_count == 584
    assert req.ssd.health_percent == 91.0
    assert req.ram.test_result == "PASS"
    assert req.thermals.max_temp_c == 96.0
    assert req.thermals.throttling_detected is True
    assert req.system.critical_errors == []


def test_battery_full_charge_exceeding_design_raises_validation_error():
    with pytest.raises(ValidationError) as exc:
        BatteryDiagnostic(
            design_capacity=50000.0,
            full_charge_capacity=60000.0,
        )
    assert "Full-charge capacity cannot exceed design capacity" in str(exc.value)


def test_endpoint_request_and_responses():
    # Products
    id_req = ProductIdentifyRequest(hint="ThinkPad T490")
    assert id_req.hint == "ThinkPad T490"

    id_resp = ProductIdentifyResponse(
        identified_model=ProductCandidate(
            manufacturer="Lenovo",
            model="ThinkPad T490",
            model_year=2019,
        ),
        visual_clues=["TrackPoint nub"],
    )
    assert id_resp.identified_model.model == "ThinkPad T490"

    # Vision
    v_req = VisionAnalyzeRequest(product_id="prod_1", image_names=["front.jpg"])
    assert v_req.product_id == "prod_1"

    v_resp = VisionAnalyzeResponse(
        product_id="prod_1",
        findings={"display": {"status": "GOOD", "observation": "Intact"}},
        overall_visual_condition="GOOD",
        evidence_items=[],
    )
    assert v_resp.overall_visual_condition == "GOOD"

    # Symptoms
    s_req = SymptomsParseRequest(product_id="prod_1", symptoms=["Battery drains fast"])
    assert len(s_req.symptoms) == 1

    s_resp = SymptomsParseResponse(product_id="prod_1", parsed_symptoms=[], evidence_items=[])
    assert s_resp.product_id == "prod_1"

    # Assessment
    a_req = AssessmentBuildRequest(product_id="prod_1")
    assert a_req.product_id == "prod_1"

    a_resp = AssessmentBuildResponse(product_id="prod_1", components={})
    assert a_resp.product_id == "prod_1"

    # Recommendations
    r_req = RecommendationsGenerateRequest(product_id="prod_1", objective=Objective.MAX_LIFE)
    assert r_req.objective == Objective.MAX_LIFE


# --- 5. Error Handling Tests ---

@pytest.fixture
def error_test_app():
    test_app = FastAPI()
    register_error_handlers(test_app)

    @test_app.get("/trigger-app-error")
    def trigger_app_error(code: str = "INVALID_DIAGNOSTIC", field: str = "battery.full_charge_capacity"):
        raise AppError(
            code=code,
            message="Full-charge capacity cannot exceed design capacity.",
            field=field,
            http_status=400,
        )

    @test_app.get("/trigger-unhandled")
    def trigger_unhandled():
        raise RuntimeError("Secret internal database connection string failed!")

    @test_app.post("/trigger-validation")
    def trigger_validation(data: BatteryDiagnostic):
        return {"status": "ok"}

    return test_app


def test_app_error_response_format(error_test_app):
    client = TestClient(error_test_app)
    res = client.get("/trigger-app-error?code=INVALID_DIAGNOSTIC&field=battery.full_charge_capacity")
    assert res.status_code == 400
    data = res.json()
    assert "error" in data
    assert data["error"] == {
        "code": "INVALID_DIAGNOSTIC",
        "message": "Full-charge capacity cannot exceed design capacity.",
        "field": "battery.full_charge_capacity",
    }


def test_all_specified_error_codes(error_test_app):
    client = TestClient(error_test_app)
    codes_to_test = [
        INVALID_INPUT,
        UNSUPPORTED_MODEL,
        INVALID_DIAGNOSTIC,
        AI_FAILURE,
        MISSING_EVIDENCE,
        INVALID_PATHWAY_CALC,
        NOT_FOUND,
    ]
    for c in codes_to_test:
        res = client.get(f"/trigger-app-error?code={c}&field=test_field")
        assert res.status_code == 400
        body = res.json()
        assert body["error"]["code"] == c
        assert body["error"]["field"] == "test_field"


def test_unhandled_exception_returns_internal_error_no_stack_trace(error_test_app):
    client = TestClient(error_test_app, raise_server_exceptions=False)
    res = client.get("/trigger-unhandled")
    assert res.status_code == 500
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == INTERNAL_ERROR
    assert data["error"]["message"] == "An unexpected internal server error occurred."
    assert data["error"]["field"] is None
    # Verify no raw exception or stack trace details leaked
    assert "Traceback" not in res.text
    assert "Secret" not in res.text


def test_request_validation_error_format(error_test_app):
    client = TestClient(error_test_app)
    # Post invalid payload (cycle_count negative)
    res = client.post("/trigger-validation", json={"cycle_count": -10})
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == INVALID_INPUT
    assert "cycle_count" in (data["error"]["field"] or "")
