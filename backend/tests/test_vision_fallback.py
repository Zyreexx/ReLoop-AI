"""
Tests for automatic multi-provider fallback strategy (Gemini -> Groq -> Demo Fallback).
Verifies:
- _is_rate_limit_error correctly identifies 429 / RESOURCE_EXHAUSTED / QuotaExceeded
- Vision analyze: Gemini 429 seamlessly falls back to Groq Llama 3.2 Vision when GROQ_API_KEY configured
- Vision identify: Gemini 429 seamlessly falls back to Groq Llama 3.2 Vision when GROQ_API_KEY configured
- Warning log "Gemini rate limit encountered. Falling back to Groq (Llama 3.2 Vision)..." is recorded
- Dual failure (Gemini + Groq) falls back to demo case handling or AI_UNAVAILABLE / 502
- When GROQ_API_KEY is not configured, Groq fallback is skipped
"""
from io import BytesIO
import logging
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.ai.gemini_client import gemini_client
from app.ai.groq_client import groq_client
from app.ai.schemas import DamageAssessmentOutput, OpenIdentificationOutput
from app.config import settings
from app.db.store import store
from app.errors import AppError, ErrorCode
from app.schemas.enums import ComponentName, ConfidenceLevel, EvidenceType
from app.schemas.product import ProductRecord
from app.services.vision import _is_rate_limit_error

VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 30


@pytest.fixture
def fallback_product() -> ProductRecord:
    prod = ProductRecord(
        id="prod_fallback_test_123",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        age=3.5,
    )
    store.save_product(prod)
    return prod


# --- 1. Unit Tests for _is_rate_limit_error ---

def test_is_rate_limit_error_detection():
    # 1. HTTP 429 in http_status
    err1 = AppError(code=ErrorCode.AI_FAILURE.value, message="Rate limited", http_status=429)
    assert _is_rate_limit_error(err1) is True

    # 2. HTTP 429 in message
    err2 = Exception("429 Client Error: Too Many Requests for url")
    assert _is_rate_limit_error(err2) is True

    # 3. RESOURCE_EXHAUSTED
    err3 = Exception("google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded")
    assert _is_rate_limit_error(err3) is True

    # 4. Quota exceeded in message
    err4 = Exception("Resource has been exhausted (e.g. check quota)")
    assert _is_rate_limit_error(err4) is True

    # 5. Rate limit exceeded in message
    err5 = AppError(code=ErrorCode.AI_FAILURE.value, message="Gemini API rate limit exceeded", http_status=502)
    assert _is_rate_limit_error(err5) is True

    # 6. Non-rate-limit errors
    err6 = Exception("Connection timed out after 30 seconds")
    assert _is_rate_limit_error(err6) is False

    err7 = AppError(code=ErrorCode.INVALID_INPUT.value, message="Invalid format", http_status=400)
    assert _is_rate_limit_error(err7) is False


# --- 2. Vision Analyze Groq Fallback Tests ---

def test_analyze_gemini_429_fails_over_to_groq(client: TestClient, fallback_product, monkeypatch, caplog):
    """
    When Gemini hits HTTP 429 / ResourceExhausted and GROQ_API_KEY is configured:
    1. Warning is logged: 'Gemini rate limit encountered. Falling back to Groq (Llama 3.2 Vision)...'
    2. Groq is invoked with the same prompt and images.
    3. Endpoint returns 200 OK with valid findings and no disruption to frontend.
    """
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_123")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    groq_damage_output = DamageAssessmentOutput(
        cracks=["Hairline crack on top display bezel"],
        dents=["Minor chassis bottom scuff"],
        missing_keys=["F4 keycap missing"],
        hinge_damage=[],
        port_damage=[],
        visible_swelling=[],
        observations=["Normal cosmetic wear"],
    )

    gemini_429_exc = AppError(
        code=ErrorCode.AI_FAILURE.value,
        message="Resource has been exhausted (e.g. check quota)",
        http_status=429,
    )

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_429_exc):
        with patch.object(groq_client, "generate_structured", return_value=groq_damage_output) as mock_groq:
            with caplog.at_level(logging.WARNING):
                files = [("images", ("laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
                res = client.post(
                    "/api/vision/analyze",
                    data={"product_id": fallback_product.id, "inspection_notes": "Inspect carefully"},
                    files=files,
                )

    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == fallback_product.id
    assert data["source"] == "live"
    assert len(data["findings"]) == 4  # crack, dent, missing key, observation

    # Check components
    components = [f["component"] for f in data["findings"]]
    assert "DISPLAY" in components
    assert "KEYBOARD" in components
    assert "HINGE_CHASSIS" in components

    # Verify Groq was called with correct parameters
    mock_groq.assert_called_once()
    _, groq_kwargs = mock_groq.call_args
    assert groq_kwargs["response_model"] == DamageAssessmentOutput
    assert len(groq_kwargs["images"]) == 1

    # Verify fallback warning log
    assert any("Gemini rate limit encountered. Falling back to Groq (Llama 3.2 Vision)..." in record.message for record in caplog.records)


# --- 3. Vision Identify Groq Fallback Tests ---

def test_identify_gemini_429_fails_over_to_groq(client: TestClient, monkeypatch, caplog):
    """
    When Gemini hits 429 during identify and GROQ_API_KEY is configured:
    Fails over to Groq and returns 200 OK with identified model.
    """
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_123")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    groq_identify_output = OpenIdentificationOutput(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        label_evidence=["Dell Latitude 5420 Regulatory Label"],
        visual_evidence=["Dell round logo", "Silver chassis"],
        contradictions=[],
        model_confidence=0.92,
    )

    gemini_429_exc = AppError(
        code=ErrorCode.AI_FAILURE.value,
        message="429 ResourceExhausted: Quota exceeded for quota metric 'GenerateContent'",
        http_status=429,
    )

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_429_exc):
        with patch.object(groq_client, "generate_structured", return_value=groq_identify_output) as mock_groq:
            with caplog.at_level(logging.WARNING):
                files = [("images", ("bottom_label.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
                res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IDENTIFIED"
    assert data["is_supported"] is True
    assert data["identified_model"]["manufacturer"] == "Dell"
    assert data["identified_model"]["model"] == "Latitude 5420"
    assert data["confidence_level"] == ConfidenceLevel.HIGH.value
    assert data["source"] == "live"

    mock_groq.assert_called_once()
    assert any("Gemini rate limit encountered. Falling back to Groq (Llama 3.2 Vision)..." in record.message for record in caplog.records)


# --- 4. Both Gemini and Groq Fail ---

def test_both_gemini_and_groq_fail_resorts_to_demo_fallback_if_enabled(client: TestClient, monkeypatch):
    """
    If both Gemini and Groq fail, falls back to demo case handling when DEMO_FALLBACK=True.
    """
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_123")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", True)

    gemini_err = AppError(code=ErrorCode.AI_FAILURE.value, message="Gemini 429 Rate Limit", http_status=429)
    groq_err = AppError(code=ErrorCode.AI_FAILURE.value, message="Groq 500 Internal Server Error", http_status=502)

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_err):
        with patch.object(groq_client, "generate_structured", side_effect=groq_err):
            files = [("images", ("thinkpad.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
            res = client.post("/api/products/identify", data={"hint": "Lenovo ThinkPad T14 Gen 1"}, files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IDENTIFIED"
    assert data["source"] == "sample-data"


def test_both_gemini_and_groq_fail_returns_ai_unavailable_if_demo_disabled(client: TestClient, monkeypatch):
    """
    If both Gemini and Groq fail and DEMO_FALLBACK=False, identify returns AI_UNAVAILABLE.
    """
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_123")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    gemini_err = AppError(code=ErrorCode.AI_FAILURE.value, message="Gemini 429 Rate Limit", http_status=429)
    groq_err = AppError(code=ErrorCode.AI_FAILURE.value, message="Groq rate limit 429", http_status=502)

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_err):
        with patch.object(groq_client, "generate_structured", side_effect=groq_err):
            files = [("images", ("device.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
            res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AI_UNAVAILABLE"


# --- 5. When GROQ_API_KEY is empty, Groq is skipped ---

def test_gemini_429_without_groq_key_skips_groq(client: TestClient, fallback_product, monkeypatch):
    """
    If GROQ_API_KEY is unset / empty, Groq fallback is skipped and original behavior is preserved.
    """
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    gemini_429_exc = AppError(
        code=ErrorCode.AI_FAILURE.value,
        message="Gemini rate limit",
        http_status=429,
    )

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_429_exc):
        with patch.object(groq_client, "generate_structured") as mock_groq:
            files = [("images", ("lid.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
            res = client.post(
                "/api/vision/analyze",
                data={"product_id": fallback_product.id},
                files=files,
            )

    assert res.status_code == 429 or res.status_code == 502
    mock_groq.assert_not_called()
