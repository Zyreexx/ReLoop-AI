"""
Comprehensive automated tests for laptop image identification reliability.
Covers all 12 scenarios specified in Phase 4:
1. Gemini identifies laptop successfully (HIGH with model digits, MEDIUM with family/visuals only).
2. Gemini returns low-confidence/uncertain result (UNKNOWN status, no fabricated model).
3. Gemini returns rate-limit/quota error and Groq succeeds.
4. Gemini fails and Groq also fails (AI_UNAVAILABLE, no fake fallback or hardcoded success).
5. Gemini returns invalid/malformed structured response and Groq succeeds.
6. Temporary provider error (500/503/timeout) triggers Groq fallback.
7. Uploaded image is empty or corrupted (400 Bad Request with clear validation error).
8. Unsupported file format (400 Bad Request).
9. Image contains a non-laptop object (UNKNOWN with informative message).
10. Image does not provide enough evidence for exact model (MEDIUM or UNKNOWN, no guessed model).
11. Conflicting visual evidence returns UNKNOWN.
12. Manual laptop selection remains available after identification failure (supported_models returned, manual selection works).
"""
import base64
from io import BytesIO
import logging
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.ai.gemini_client import gemini_client
from app.ai.groq_client import groq_client
from app.ai.schemas import OpenIdentificationOutput
from app.config import settings
from app.errors import AppError, ErrorCode
from app.schemas.enums import ConfidenceLevel, IdentificationStatus

VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 30
VALID_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 30
CORRUPTED_BYTES = b"NOT_A_VALID_IMAGE_HEADER_12345"


# 1. Gemini identifies laptop successfully
def test_scenario_01_gemini_identifies_laptop_successfully_high_and_medium(client: TestClient):
    # 1a. HIGH confidence when specific model designator is verified in label evidence
    ai_output_high = OpenIdentificationOutput(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        label_evidence=["Dell Latitude 5420 Regulatory Label"],
        visual_evidence=["Dell logo on silver lid"],
        contradictions=[],
        model_confidence=0.95,
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output_high):
        files = [("images", ("dell.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.IDENTIFIED.value
    assert data["identified_model"]["manufacturer"] == "Dell"
    assert data["identified_model"]["model"] == "Latitude 5420"
    assert data["confidence_level"] == ConfidenceLevel.HIGH.value

    # 1b. MEDIUM confidence when only family name is present without specific model digits
    ai_output_medium = OpenIdentificationOutput(
        manufacturer="Lenovo",
        model="ThinkPad",
        model_year=2021,
        label_evidence=["ThinkPad logo sticker"],
        visual_evidence=["Red TrackPoint nub on keyboard"],
        contradictions=[],
        model_confidence=0.80,
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output_medium):
        files = [("images", ("thinkpad.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res_med = client.post("/api/products/identify", files=files)

    assert res_med.status_code == 200
    data_med = res_med.json()
    assert data_med["status"] == IdentificationStatus.IDENTIFIED.value
    assert data_med["confidence_level"] == ConfidenceLevel.MEDIUM.value


# 2. Gemini returns low-confidence/uncertain result
def test_scenario_02_gemini_returns_uncertain_result(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="UNKNOWN",
        model="UNKNOWN",
        model_year=None,
        label_evidence=[],
        visual_evidence=["Unclear dark surface"],
        contradictions=[],
        model_confidence=0.15,
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("blur.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.UNKNOWN.value
    assert data["identified_model"] is None
    assert "could not be identified" in data["message"].lower()


# 3. Gemini returns rate-limit/quota error and Groq succeeds
def test_scenario_03_gemini_rate_limit_groq_succeeds(client: TestClient, monkeypatch, caplog):
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_scenario3")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    groq_output = OpenIdentificationOutput(
        manufacturer="HP",
        model="EliteBook 840 G7",
        model_year=2020,
        label_evidence=["HP EliteBook 840 G7"],
        visual_evidence=["Silver aluminum chassis", "HP slash logo"],
        contradictions=[],
        model_confidence=0.92,
    )
    gemini_429 = AppError(
        code=ErrorCode.AI_FAILURE.value,
        message="429 ResourceExhausted: Quota exceeded",
        http_status=429,
    )

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_429):
        with patch.object(groq_client, "generate_structured", return_value=groq_output) as mock_groq:
            with caplog.at_level(logging.WARNING):
                files = [("images", ("hp.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
                res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.IDENTIFIED.value
    assert data["identified_model"]["manufacturer"] == "HP"
    assert data["identified_model"]["model"] == "EliteBook 840 G7"
    mock_groq.assert_called_once()
    assert any("Gemini rate limit encountered. Falling back to Groq (Llama 3.2 Vision)..." in r.message for r in caplog.records)


# 4. Gemini fails and Groq also fails (AI_UNAVAILABLE)
def test_scenario_04_gemini_and_groq_both_fail_returns_ai_unavailable(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_scenario4")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    gemini_err = AppError(code=ErrorCode.AI_FAILURE.value, message="Gemini 429 Rate Limit", http_status=429)
    groq_err = AppError(code=ErrorCode.AI_FAILURE.value, message="Groq 503 Service Unavailable", http_status=503)

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_err):
        with patch.object(groq_client, "generate_structured", side_effect=groq_err):
            files = [("images", ("laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
            res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.AI_UNAVAILABLE.value
    assert data["source"] != "sample-data"
    assert data["identified_model"] is None
    assert "temporarily unavailable" in data["message"].lower()


# 5. Gemini returns invalid/malformed structured response and Groq succeeds
def test_scenario_05_gemini_malformed_response_triggers_groq_fallback(client: TestClient, monkeypatch, caplog):
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_scenario5")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    groq_output = OpenIdentificationOutput(
        manufacturer="Apple",
        model="MacBook Air (M1, 2020)",
        model_year=2020,
        label_evidence=["Model A2337 EMC 3598"],
        visual_evidence=["Apple logo", "Wedge-shaped unibody aluminum chassis"],
        contradictions=[],
        model_confidence=0.95,
    )
    gemini_json_err = ValueError("Unterminated string starting at line 1 column 45 (char 44)")

    with patch.object(gemini_client, "generate_structured", side_effect=gemini_json_err):
        with patch.object(groq_client, "generate_structured", return_value=groq_output) as mock_groq:
            with caplog.at_level(logging.WARNING):
                files = [("images", ("macbook.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
                res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.IDENTIFIED.value
    assert data["identified_model"]["manufacturer"] == "Apple"
    mock_groq.assert_called_once()
    assert any("Falling back to Groq (Llama 3.2 Vision)..." in r.message for r in caplog.records)


# 6. Temporary provider error (500/503/timeout) triggers Groq fallback
def test_scenario_06_temporary_provider_error_triggers_groq(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.config.settings.GROQ_API_KEY", "test_groq_key_scenario6")
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)

    groq_output = OpenIdentificationOutput(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        label_evidence=["Latitude 5420"],
        visual_evidence=["Dell circular logo"],
        contradictions=[],
        model_confidence=0.90,
    )
    timeout_err = TimeoutError("Connection to Gemini API timed out after 30000ms")

    with patch.object(gemini_client, "generate_structured", side_effect=timeout_err):
        with patch.object(groq_client, "generate_structured", return_value=groq_output) as mock_groq:
            files = [("images", ("dell.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
            res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.IDENTIFIED.value
    assert data["identified_model"]["model"] == "Latitude 5420"
    mock_groq.assert_called_once()


# 7. Uploaded image is empty or corrupted
def test_scenario_07_empty_or_corrupted_image(client: TestClient):
    # 7a. 0-byte file
    files_empty = [("images", ("empty.jpg", BytesIO(b""), "image/jpeg"))]
    res_empty = client.post("/api/products/identify", files=files_empty)
    assert res_empty.status_code == 400
    assert res_empty.json()["error"]["code"] == ErrorCode.INVALID_INPUT.value

    # 7b. Corrupted magic bytes
    files_corrupt = [("images", ("corrupted.jpg", BytesIO(CORRUPTED_BYTES), "image/jpeg"))]
    res_corrupt = client.post("/api/products/identify", files=files_corrupt)
    assert res_corrupt.status_code == 400
    assert res_corrupt.json()["error"]["code"] == ErrorCode.INVALID_INPUT.value
    assert "unsupported image format" in res_corrupt.json()["error"]["message"].lower()


# 8. Unsupported file format
def test_scenario_08_unsupported_file_format(client: TestClient):
    text_content = b"This is a text file, not an image."
    files = [("images", ("document.txt", BytesIO(text_content), "text/plain"))]
    res = client.post("/api/products/identify", files=files)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == ErrorCode.INVALID_INPUT.value


# 9. Image contains a non-laptop object
def test_scenario_09_non_laptop_object_returns_rejected(client: TestClient):
    ai_output_phone = OpenIdentificationOutput(
        manufacturer="Apple",
        model="iPhone 13",
        model_year=2021,
        label_evidence=[],
        visual_evidence=["Smartphone device on desk, not a laptop"],
        contradictions=["Non-laptop object detected"],
        model_confidence=0.85,
        is_laptop=False,
        detected_device_type="SMARTPHONE",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output_phone):
        files = [("images", ("phone.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.NON_LAPTOP_REJECTED.value
    assert data["identified_model"] is None
    assert data["is_laptop"] is False
    assert data["allow_manual_selection"] is False
    assert "smartphone" in data["message"].lower() or "laptop" in data["message"].lower()


# 10. Image does not provide enough evidence for exact model
def test_scenario_10_insufficient_evidence_for_exact_model(client: TestClient):
    # Generic chassis with no branding or labels
    ai_output = OpenIdentificationOutput(
        manufacturer="GenericBrand",
        model="Laptop 15",
        model_year=2022,
        label_evidence=[],
        visual_evidence=["Dark gray laptop chassis"],
        contradictions=[],
        model_confidence=0.45,
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("generic.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    # Confidence must not be HIGH; it caps at LOW or UNKNOWN
    assert data["confidence_level"] in (ConfidenceLevel.LOW.value, ConfidenceLevel.UNKNOWN.value)
    assert data["needs_confirmation"] is True


# 11. Conflicting visual evidence returns UNKNOWN
def test_scenario_11_conflicting_visual_evidence_returns_unknown(client: TestClient):
    ai_output_conflict = OpenIdentificationOutput(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        label_evidence=["Lenovo serial sticker 1S20VYS0A00"],
        visual_evidence=["Round Dell logo on top lid"],
        contradictions=["Contradiction: Dell logo on lid conflicts with Lenovo serial sticker"],
        model_confidence=0.90,
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output_conflict):
        files = [("images", ("mixed.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.UNKNOWN.value
    assert data["identified_model"] is None
    assert data["confidence_level"] == ConfidenceLevel.UNKNOWN.value


# 12. Manual laptop selection remains available after identification failure
def test_scenario_12_manual_laptop_selection_available_after_failure(client: TestClient):
    # 12a. When identification returns UNKNOWN, supported_models catalog is provided
    ai_output_unknown = OpenIdentificationOutput(
        manufacturer="UNKNOWN",
        model="UNKNOWN",
        model_year=None,
        label_evidence=[],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.0,
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output_unknown):
        files = [("images", ("unknown.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res_fail = client.post("/api/products/identify", files=files)

    assert res_fail.status_code == 200
    data_fail = res_fail.json()
    assert data_fail["status"] == IdentificationStatus.UNKNOWN.value
    assert len(data_fail["supported_models"]) >= 4

    # 12b. User can select model manually via manual_model
    with patch.object(gemini_client, "generate_structured") as mock_gemini:
        res_manual = client.post(
            "/api/products/identify",
            json={"manual_model": "Dell Latitude 5420"},
        )
        assert res_manual.status_code == 200
        mock_gemini.assert_not_called()
        data_manual = res_manual.json()
        assert data_manual["is_supported"] is True
        assert data_manual["identified_model"]["manufacturer"] == "Dell"
        assert data_manual["identified_model"]["model"] == "Latitude 5420"
        assert data_manual["source"] == "manual"


# Extra: Base64 JSON image identify support
def test_base64_json_image_identify_support(client: TestClient):
    b64_image = base64.b64encode(VALID_JPEG).decode("ascii")
    ai_output = OpenIdentificationOutput(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        label_evidence=["Dell Latitude 5420 Regulatory Label"],
        visual_evidence=["Silver chassis"],
        contradictions=[],
        model_confidence=0.92,
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        res = client.post(
            "/api/products/identify",
            json={"image_base64": b64_image},
        )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.IDENTIFIED.value
    assert data["identified_model"]["model"] == "Latitude 5420"

