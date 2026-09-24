"""
Tests for PostgreSQL / SQLite persistence, ORM models, repository layer, and DB product routes.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db.base import Base
from app.db.session import get_db
from app.db.repositories import (
    product_repo,
    evidence_repo,
    assessment_repo,
    recommendation_repo,
)
from app.main import app
from app.models.entities import (
    Product as ProductModel,
    Assessment as AssessmentModel,
    Evidence as EvidenceModel,
    ComponentConditionRecord as ComponentConditionModel,
    RecommendationRecord as RecommendationModel,
)
from app.schemas.enums import (
    ComponentName,
    ComponentStatus,
    ConfidenceLevel,
    DeviceCategory,
    EvidenceType,
    Objective,
    PathwayType,
)
from app.schemas.product import Product, ProductCreate, ProductSpecs
from app.schemas.evidence import Evidence
from app.schemas.condition import AssessmentBuildResponse, ComponentCondition
from app.schemas.recommendation import Recommendation, ScoredPathway
from app.schemas.pathway import Pathway, PathwayEligibility, EnvironmentalEstimate, LogisticsEstimate
from app.schemas.estimate import Estimate


# In-memory SQLite engine with StaticPool for test isolation
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# 1. Test Product Repository & ORM
# ---------------------------------------------------------------------------

def test_product_repository_create_and_get(db_session):
    create_dto = ProductCreate(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        category=DeviceCategory.LAPTOP,
        serial_or_identifier="DELL-SN-12345",
        age_years=4.5,
    )
    product = product_repo.create(db_session, create_dto)

    assert product.id.startswith("prod_")
    assert product.manufacturer == "Dell"
    assert product.model == "Latitude 5420"
    assert product.model_year == 2021
    assert product.age == 4.5
    assert product.specs.ram_modular is True

    # Retrieve from DB
    fetched = product_repo.get_by_id(db_session, product.id)
    assert fetched is not None
    assert fetched.id == product.id
    assert fetched.model == "Latitude 5420"
    assert fetched.specs.battery_replaceable is True


def test_product_repository_get_nonexistent(db_session):
    fetched = product_repo.get_by_id(db_session, "nonexistent_id")
    assert fetched is None


# ---------------------------------------------------------------------------
# 2. Test Evidence Repository & ORM
# ---------------------------------------------------------------------------

def test_evidence_repository_add_and_query(db_session):
    product = product_repo.create(
        db_session,
        ProductCreate(
            manufacturer="Lenovo",
            model="ThinkPad T14 Gen 1",
            model_year=2020,
            age_years=5.0,
        ),
    )

    ev1 = Evidence(
        product_id=product.id,
        type=EvidenceType.DIAGNOSTIC,
        source="Windows Battery Report (powercfg)",
        component="battery",
        value={"design_mwh": 50000, "full_mwh": 37500, "health_percent": 75.0, "cycles": 420},
        confidence=ConfidenceLevel.HIGH,
    )
    ev2 = Evidence(
        product_id=product.id,
        type=EvidenceType.VISUAL,
        source="Chassis Photo Inspection",
        component="keyboard",
        value={"missing_keys": ["W", "E"], "visible_status": "SERVICE_REQUIRED"},
        confidence=ConfidenceLevel.HIGH,
    )

    saved_ev1 = evidence_repo.add(db_session, ev1, product_id=product.id)
    saved_ev2 = evidence_repo.add(db_session, ev2, product_id=product.id)

    assert saved_ev1.id.startswith("ev_")
    assert saved_ev1.value["health_percent"] == 75.0

    # Query all evidence for product
    all_ev = evidence_repo.get_by_product_id(db_session, product.id)
    assert len(all_ev) == 2
    sources = [e.source for e in all_ev]
    assert "Windows Battery Report (powercfg)" in sources
    assert "Chassis Photo Inspection" in sources


# ---------------------------------------------------------------------------
# 3. Test Assessment Repository & Component Condition Records
# ---------------------------------------------------------------------------

def test_assessment_repository_save_and_get(db_session):
    product = product_repo.create(
        db_session,
        ProductCreate(
            manufacturer="Dell",
            model="Latitude 5420",
            model_year=2021,
            age_years=4.0,
        ),
    )

    battery_comp = ComponentCondition(
        component=ComponentName.BATTERY,
        status=ComponentStatus.SERVICE_REQUIRED,
        observations=["Battery capacity degraded to 73%."],
        measurements={"health_percentage": "73%", "cycle_count": "482"},
        confidence=ConfidenceLevel.HIGH,
        evidence_ids=["ev_batt_01"],
        repairable=True,
    )
    ssd_comp = ComponentCondition(
        component=ComponentName.SSD,
        status=ComponentStatus.GOOD,
        observations=["SMART health normal, 0 critical sectors."],
        measurements={"health_percentage": "95%", "smart_status": "PASS"},
        confidence=ConfidenceLevel.HIGH,
        evidence_ids=["ev_ssd_01"],
        repairable=True,
    )

    evidence_item = Evidence(
        product_id=product.id,
        type=EvidenceType.DIAGNOSTIC,
        source="Hardware Battery Telemetry",
        component="battery",
        value={"health_percentage": 73.0},
    )

    assessment_dto = AssessmentBuildResponse(
        product_id=product.id,
        overall_hardware_health="FAIR",
        components={"battery": battery_comp, "ssd": ssd_comp},
        all_evidence=[evidence_item],
    )

    saved_asm = assessment_repo.save(db_session, assessment_dto)
    assert saved_asm.product_id == product.id
    assert saved_asm.overall_hardware_health == "FAIR"

    # Fetch assessment back
    fetched_asm = assessment_repo.get_by_product_id(db_session, product.id)
    assert fetched_asm is not None
    assert "battery" in fetched_asm.components
    assert fetched_asm.components["battery"].status == ComponentStatus.SERVICE_REQUIRED
    assert fetched_asm.components["battery"].measurements["health_percentage"] == "73%"
    assert "ssd" in fetched_asm.components
    assert fetched_asm.components["ssd"].status == ComponentStatus.GOOD


# ---------------------------------------------------------------------------
# 4. Test Recommendation Repository & Records
# ---------------------------------------------------------------------------

def test_recommendation_repository_save_and_get(db_session):
    product = product_repo.create(
        db_session,
        ProductCreate(
            manufacturer="Dell",
            model="Latitude 5420",
            model_year=2021,
            age_years=4.0,
        ),
    )

    pathway = Pathway(
        type=PathwayType.REPAIR,
        eligibility=PathwayEligibility(is_eligible=True, reasons=["Battery is replaceable"]),
        estimated_cost=Estimate(value_min=50.0, value_max=85.0, unit="USD", basis="REPAIR_CATALOG"),
        expected_life_extension=Estimate(value_min=2.0, value_max=3.5, unit="years", basis="LIFECYCLE_MODEL"),
        value_retained=85.0,
        material_retained=92.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=180.0, co2_avoided_kg_max=240.0, ewaste_diverted_kg=1.4
        ),
        logistics=LogisticsEstimate(complexity="LOW", turnaround_days_min=1, turnaround_days_max=3),
        actions_required=["Replace battery pack with OEM part", "Clean heatsink and repaste thermal paste"],
        assumptions=["Genuine or certified OEM replacement cells available"],
    )

    rec_dto = Recommendation(
        product_id=product.id,
        selected_pathway=PathwayType.REPAIR,
        objective=Objective.MAX_LIFE,
        score=88.5,
        primary_recommendation=ScoredPathway(pathway=pathway, score=88.5, rank=1),
        alternative_pathways=[],
        reasoning=[
            "Battery capacity has degraded below threshold.",
            "SSD and memory diagnostics pass with 95%+ integrity.",
        ],
        evidence_ids=["ev_1", "ev_2"],
        assumptions=["Assumes standard technician repair turnaround of 1-3 business days."],
    )

    saved_rec = recommendation_repo.save(db_session, rec_dto)
    assert saved_rec.id.startswith("rec_")
    assert saved_rec.score == 88.5

    # Retrieve recommendation by product ID
    fetched_rec = recommendation_repo.get_by_product_id(db_session, product.id)
    assert fetched_rec is not None
    assert fetched_rec.selected_pathway == PathwayType.REPAIR
    assert fetched_rec.objective == Objective.MAX_LIFE
    assert len(fetched_rec.reasoning) == 2
    assert "Battery capacity has degraded" in fetched_rec.reasoning[0]


# ---------------------------------------------------------------------------
# 5. Test API Routes with Database (POST /api/products, GET /api/products/{id})
# ---------------------------------------------------------------------------

def test_api_create_and_get_product(client):
    payload = {
        "manufacturer": "Dell",
        "model": "Latitude 5420",
        "model_year": 2021,
        "category": "LAPTOP",
        "serial_or_identifier": "TEST-SN-9988",
        "age_years": 4.5,
    }
    # 1. POST /api/products
    res = client.post("/api/products", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["id"].startswith("prod_")
    assert data["manufacturer"] == "Dell"
    assert data["model"] == "Latitude 5420"
    assert data["model_year"] == 2021
    product_id = data["id"]

    # 2. GET /api/products/{id}
    get_res = client.get(f"/api/products/{product_id}")
    assert get_res.status_code == 200
    get_data = get_res.json()
    assert get_data["id"] == product_id
    assert get_data["model"] == "Latitude 5420"
    assert get_data["specs"]["ram_modular"] is True


def test_api_get_product_not_found(client):
    res = client.get("/api/products/nonexistent_product_12345")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["field"] == "product_id"
