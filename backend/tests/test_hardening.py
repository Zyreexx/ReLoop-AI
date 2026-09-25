"""
Security, error-handling, upload validation, CORS, idempotency, and logging hardening tests.
"""
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.db.store import store
from app.schemas.enums import DeviceCategory, Objective
from app.schemas.product import ProductCreate, ProductSpecs


@pytest.fixture
def test_client():
    return TestClient(app)


# --- 1. Error Response Format & No Stack Trace Leaks ---

def test_error_shape_on_not_found(test_client):
    """
    HTTP 404 Not Found returns exact {"error": {"code", "message", "field"}} shape.
    """
    res = test_client.get("/api/nonexistent_route_404")
    assert res.status_code == 404
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == "NOT_FOUND"
    assert "message" in body["error"]
    assert "field" in body["error"]
    # Ensure no traceback or internal code lines leaked
    assert "Traceback" not in res.text


def test_error_shape_on_validation_error(test_client):
    """
    422 Unprocessable Entity returns exact {"error": {"code", "message", "field"}} shape.
    """
    # Send malformed JSON payload missing required fields
    res = test_client.post("/api/products", json={"invalid_field": 123})
    assert res.status_code == 422
    body = res.json()
    assert "error" in body
    assert body["error"]["code"] == "INVALID_INPUT"
    assert body["error"]["field"] is not None
    assert "Traceback" not in res.text


def test_error_shape_on_unhandled_server_error(test_client, monkeypatch):
    """
    500 Internal Server Error returns generic INTERNAL_ERROR with zero stack traces leaked to client.
    """
    from app.services.product_service import product_service

    def mock_broken_get(*args, **kwargs):
        raise RuntimeError("SecretDatabaseCrashException: password=secret123 in line 42")

    monkeypatch.setattr(product_service, "get_by_id", mock_broken_get)

    res = test_client.get("/api/products/prod_crash_test")
    assert res.status_code == 500
    body = res.json()
    assert body == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "An unexpected internal server error occurred.",
            "field": None,
        }
    }
    assert "secret123" not in res.text
    assert "Traceback" not in res.text


# --- 2. CORS Restriction ---

def test_cors_restricted_not_wildcard():
    """
    CORS origins must be explicit from environment, not wildcard '*'.
    """
    assert "*" not in settings.CORS_ORIGINS
    assert len(settings.CORS_ORIGINS) >= 1
    for origin in settings.CORS_ORIGINS:
        assert origin.startswith("http://") or origin.startswith("https://")


# --- 3. Upload Validation & Security ---

def test_upload_rejects_fake_extension_with_invalid_magic_bytes(test_client):
    """
    A text file disguised as 'image.jpg' must be rejected based on real file contents, not filename extension.
    """
    fake_jpg_content = b"This is plain text disguised as an image file."
    files = [("images", ("malicious.jpg", fake_jpg_content, "image/jpeg"))]
    data = {"product_id": "prod_123"}

    res = test_client.post("/api/vision/analyze", data=data, files=files)
    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "INVALID_INPUT"
    assert "Unsupported image format" in body["error"]["message"]


def test_upload_rejects_oversized_file(test_client, monkeypatch):
    """
    Files exceeding MAX_UPLOAD_MB must be rejected.
    """
    monkeypatch.setattr(settings, "MAX_UPLOAD_MB", 1)  # Set 1MB limit for testing
    oversized_bytes = b"\xff\xd8\xff" + b"0" * (2 * 1024 * 1024)  # 2MB JPEG
    files = [("images", ("large.jpg", oversized_bytes, "image/jpeg"))]
    data = {"product_id": "prod_123"}

    res = test_client.post("/api/vision/analyze", data=data, files=files)
    assert res.status_code == 400
    body = res.json()
    assert body["error"]["code"] == "INVALID_INPUT"
    assert "exceeds maximum allowed size" in body["error"]["message"]


def test_filename_sanitization():
    """
    Upload filenames must be sanitized to strip path traversal sequences like '../../'.
    """
    from app.utils.uploads import sanitize_filename
    assert sanitize_filename("../../etc/passwd.jpg") == "passwd.jpg"
    assert sanitize_filename("..\\..\\windows\\system32.png") == "system32.png"
    assert sanitize_filename("valid_image-123.jpg") == "valid_image-123.jpg"


# --- 4. Idempotency on Create Endpoints ---

def test_product_creation_idempotency(test_client):
    """
    Submitting the same product registration multiple times is idempotent.
    """
    payload = {
        "manufacturer": "Dell",
        "model": "Latitude 5420",
        "model_year": 2021,
        "category": "LAPTOP",
        "serial_or_identifier": "SN-LATITUDE-5420-IDEMPOTENT",
    }

    res1 = test_client.post("/api/products", json=payload)
    assert res1.status_code == 200
    prod_id_1 = res1.json()["id"]

    res2 = test_client.post("/api/products", json=payload)
    assert res2.status_code == 200
    prod_id_2 = res2.json()["id"]

    # Same product returned without duplicate key violation
    assert prod_id_1 == prod_id_2


def test_assessment_and_recommendation_idempotency(test_client):
    """
    Resubmitting assessment build and recommendation generation for the same product does not crash or create duplicates.
    """
    # 1. Create product
    prod_res = test_client.post("/api/products", json={
        "manufacturer": "Dell",
        "model": "Latitude 5420",
        "model_year": 2021,
        "category": "LAPTOP",
    })
    prod_id = prod_res.json()["id"]

    # 2. Build assessment multiple times
    build_res_1 = test_client.post("/api/assessment/build", json={"product_id": prod_id})
    assert build_res_1.status_code == 200

    build_res_2 = test_client.post("/api/assessment/build", json={"product_id": prod_id})
    assert build_res_2.status_code == 200
    assert build_res_1.json()["product_id"] == build_res_2.json()["product_id"]

    # 3. Generate recommendation multiple times
    rec_res_1 = test_client.post("/api/recommendations/generate", json={"product_id": prod_id, "objective": "MAX_LIFE"})
    assert rec_res_1.status_code == 200

    rec_res_2 = test_client.post("/api/recommendations/generate", json={"product_id": prod_id, "objective": "MAX_LIFE"})
    assert rec_res_2.status_code == 200
    assert rec_res_1.json()["selected_pathway"] == rec_res_2.json()["selected_pathway"]


# --- 5. Structured Request Logging & X-Request-ID ---

def test_request_logging_propagates_request_id(test_client):
    """
    Responses carry X-Request-ID header generated by structured logging middleware.
    """
    res = test_client.get("/health")
    assert res.status_code == 200
    assert "X-Request-ID" in res.headers
    assert res.headers["X-Request-ID"].startswith("req_")

    # Custom request ID passed by client is preserved
    custom_id = "req_custom_test_12345"
    res_custom = test_client.get("/health", headers={"X-Request-ID": custom_id})
    assert res_custom.status_code == 200
    assert res_custom.headers["X-Request-ID"] == custom_id
