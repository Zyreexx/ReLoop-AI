"""
Tests for Location-Based Repair Shop & Certified E-Waste Recycler Locator.
Validates geospatial search, Haversine formula, R2v3 / e-Stewards certification checks,
and category filtering.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.locator_service import haversine_distance_km, locator_service
from app.knowledge.recycler_certifications import verify_facility_certification

client = TestClient(app)


def test_haversine_distance():
    # Distance between London (51.5074, -0.1278) and Paris (48.8566, 2.3522) is approx 343 km
    dist = haversine_distance_km(51.5074, -0.1278, 48.8566, 2.3522)
    assert 340.0 <= dist <= 350.0


def test_certification_directory_verification():
    # Verified facility
    v1 = verify_facility_certification("Sims Lifecycle Services Pune Branch")
    assert v1 is not None
    assert "R2v3" in v1["standard"]
    assert v1["verification_status"] == "ACTIVE_VERIFIED"

    # Non-certified local scrap dealer
    v2 = verify_facility_certification("Joe's Unofficial Metal Scrap Yard")
    assert v2 is None


def test_locator_search_endpoint_default():
    resp = client.get("/api/locator/search")
    assert resp.status_code == 200
    data = resp.json()
    assert "query_location" in data
    assert "results" in data
    assert len(data["results"]) >= 1
    first = data["results"][0]
    assert "name" in first
    assert "category" in first
    assert "distance_km" in first
    assert "directions_url" in first
    assert "is_certified" in first


def test_locator_search_category_filter():
    # Repair only
    resp_rep = client.get("/api/locator/search", params={"category": "REPAIR", "query": "Pune"})
    assert resp_rep.status_code == 200
    rep_results = resp_rep.json()["results"]
    for r in rep_results:
        assert r["category"] == "REPAIR_SHOP"

    # Recycle only
    resp_rec = client.get("/api/locator/search", params={"category": "RECYCLE", "query": "Pune"})
    assert resp_rec.status_code == 200
    rec_results = resp_rec.json()["results"]
    for r in rec_results:
        assert r["category"] in ["CERTIFIED_RECYCLER", "E_WASTE_COLLECTOR"]


def test_locator_certifications_info_endpoint():
    resp = client.get("/api/locator/certifications")
    assert resp.status_code == 200
    standards = resp.json()
    assert isinstance(standards, list)
    names = [s["standard_name"] for s in standards]
    assert any("R2v3" in n for n in names)
    assert any("e-Stewards" in n for n in names)

