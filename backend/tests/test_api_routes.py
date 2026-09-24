"""
End-to-end API route tests using FastAPI TestClient.
"""
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_products_catalog(client: TestClient):
    res = client.get("/api/products/catalog")
    assert res.status_code == 200
    models = res.json()
    assert len(models) >= 3
    names = [f"{m['manufacturer']} {m['model']}" for m in models]
    assert any("Dell" in n for n in names)
    assert any("ThinkPad" in n for n in names)


def test_product_identification_and_registration(client: TestClient):
    # 1. Identify product
    id_res = client.post(
        "/api/products/identify",
        json={"manual_model": "Dell Latitude 5420"},
    )
    assert id_res.status_code == 200
    id_data = id_res.json()
    assert id_data["identified_model"]["manufacturer"] == "Dell"
    assert id_data["identified_model"]["model"] == "Latitude 5420"
    assert id_data["requires_user_confirmation"] is True

    # 2. Confirm and create product
    create_res = client.post(
        "/api/products",
        json={
            "manufacturer": "Dell",
            "model": "Latitude 5420",
            "model_year": 2021,
            "category": "LAPTOP",
            "age_years": 4.5,
        },
    )
    assert create_res.status_code == 200
    prod = create_res.json()
    prod_id = prod["id"]
    assert prod_id.startswith("prod_")

    # 3. Retrieve by ID
    get_res = client.get(f"/api/products/{prod_id}")
    assert get_res.status_code == 200
    assert get_res.json()["model"] == "Latitude 5420"


def test_full_circular_assessment_journey(client: TestClient):
    # Step 1: Register product
    prod_res = client.post(
        "/api/products",
        json={
            "manufacturer": "Dell",
            "model": "Latitude 5420",
            "model_year": 2021,
            "category": "LAPTOP",
        },
    )
    prod_id = prod_res.json()["id"]

    # Step 2: Optical inspection
    vis_res = client.post(
        "/api/vision/analyze",
        json={
            "product_id": prod_id,
            "image_names": ["dell_front.jpg", "dell_keyboard.jpg"],
            "inspection_notes": "Missing W keycap, minor corner scratches",
        },
    )
    assert vis_res.status_code == 200
    assert len(vis_res.json()["evidence_items"]) > 0

    # Step 3: Hardware Diagnostics
    diag_res = client.post(
        "/api/diagnostics/validate",
        json={
            "product_id": prod_id,
            "battery": {
                "design_capacity_mwh": 58000.0,
                "full_charge_capacity_mwh": 42340.0,
                "cycle_count": 584,
            },
            "ssd": {
                "smart_status": "PASS",
                "health_percentage": 91.0,
            },
            "ram": {
                "memory_test_status": "PASS",
                "installed_gb": 16,
            },
            "thermals": {
                "cpu_idle_temp_c": 48.0,
                "cpu_max_temp_c": 96.0,
                "throttling_detected": True,
            },
        },
    )
    assert diag_res.status_code == 200
    assert diag_res.json()["valid"] is True

    # Step 4: Symptoms
    symp_res = client.post(
        "/api/symptoms/parse",
        json={
            "product_id": prod_id,
            "selected_symptoms": ["Battery drains quickly", "Fans get loud"],
            "user_notes": "Laptop gets very warm while on video calls.",
            "intended_use": "daily_office_and_web",
        },
    )
    assert symp_res.status_code == 200

    # Step 5: Build Assessment
    assess_res = client.post(
        "/api/assessment/build",
        json={"product_id": prod_id},
    )
    assert assess_res.status_code == 200
    profile = assess_res.json()
    assert "battery" in profile["components"]
    assert "ssd" in profile["components"]
    assert "thermals" in profile["components"]

    # Step 6: Generate Recommendation
    rec_res = client.post(
        "/api/recommendations/generate",
        json={
            "product_id": prod_id,
            "objective": "MAXIMUM_LIFE",
        },
    )
    assert rec_res.status_code == 200
    rec = rec_res.json()
    assert rec["selected_pathway"] in ["REPAIR", "REFURBISH"]
    assert len(rec["reasoning"]) > 0
    assert len(rec["explicit_assumptions"]) > 0

    # Step 7: Retrieve report by ID
    report_res = client.get(f"/api/reports/{rec['id']}")
    assert report_res.status_code == 200
    assert report_res.json()["id"] == rec["id"]


def test_typed_error_format_on_validation_failure(client: TestClient):
    """
    Test that invalid inputs adhere to the rules.md format:
    {
      "error": {
        "code": "...",
        "message": "...",
        "field": "..."
      }
    }
    """
    res = client.post(
        "/api/diagnostics/validate",
        json={
            "product_id": "non_existent",
            "battery": {
                "design_capacity_mwh": 50000.0,
                "full_charge_capacity_mwh": 70000.0,  # Invalid: full > design
            },
        },
    )
    assert res.status_code in [400, 422]
    body = res.json()
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "field" in body["error"]
