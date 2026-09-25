"""
Unit and integration tests for:
- POST /api/products/identify (image upload, manual fallback, unknown model, Gemini failure)
- POST /api/vision/analyze (image upload, post-filter dropping internal claims, evidence persistence, Gemini failure)
- Upload handling (magic bytes validation, file size limits, filename sanitization)
- Post-filter non-negotiable rule: a photo can NEVER prove internal battery/SSD/RAM/motherboard health.
"""
from io import BytesIO
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.ai.gemini_client import gemini_client
from app.ai.schemas import ModelIdentificationOutput, DamageAssessmentOutput
from app.config import settings
from app.db.store import store
from app.errors import AppError, ErrorCode
from app.schemas.enums import ComponentName, EvidenceType
from app.schemas.product import ProductRecord
from app.schemas.vision import VisibleFinding
from app.services.vision import filter_visible_findings


# Mock image bytes with valid magic headers
VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 30
VALID_PNG = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 30
VALID_WEBP = b"RIFF\x24\x00\x00\x00WEBPVP8 " + b"\x00" * 30
INVALID_IMAGE = b"Not a real image file content for testing magic bytes"


@pytest.fixture
def registered_product() -> ProductRecord:
    prod = ProductRecord(
        id="prod_test_vision_123",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        age=4.5,
    )
    store.save_product(prod)
    return prod


# ============================================================================
# 1. Upload Validation Tests
# ============================================================================

def test_identify_rejects_invalid_magic_bytes(client: TestClient):
    files = [("images", ("fake.jpg", BytesIO(INVALID_IMAGE), "image/jpeg"))]
    res = client.post("/api/products/identify", files=files)
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value
    assert "unsupported image format" in err["message"].lower()


def test_identify_rejects_oversized_file(client: TestClient):
    oversized_data = VALID_JPEG + b"\x00" * ((settings.MAX_UPLOAD_MB + 1) * 1024 * 1024)
    files = [("images", ("huge.jpg", BytesIO(oversized_data), "image/jpeg"))]
    res = client.post("/api/products/identify", files=files)
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value
    assert "exceeds maximum allowed size" in err["message"].lower()


def test_identify_rejects_more_than_max_files(client: TestClient):
    files = [
        ("images", ("pic1.jpg", BytesIO(VALID_JPEG), "image/jpeg")),
        ("images", ("pic2.png", BytesIO(VALID_PNG), "image/png")),
        ("images", ("pic3.webp", BytesIO(VALID_WEBP), "image/webp")),
        ("images", ("pic4.jpg", BytesIO(VALID_JPEG), "image/jpeg")),
    ]
    res = client.post("/api/products/identify", files=files)
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value
    assert "maximum of 3 images" in err["message"].lower()


def test_identify_rejects_empty_file(client: TestClient):
    files = [("images", ("empty.jpg", BytesIO(b""), "image/jpeg"))]
    res = client.post("/api/products/identify", files=files)
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value


# ============================================================================
# 2. Product Identification Tests
# ============================================================================

def test_identify_success_with_images_and_mocked_gemini(client: TestClient):
    mock_ai_output = ModelIdentificationOutput(
        model_name="Dell Latitude 5420",
        confidence=0.92,
        visible_label_text="Latitude 5420 Reg Model P137G",
        visual_clues=["Dell emblem", "Right side wedge lock"],
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [
            ("images", ("front.jpg", BytesIO(VALID_JPEG), "image/jpeg")),
            ("images", ("bottom.png", BytesIO(VALID_PNG), "image/png")),
        ]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is True
    assert data["confidence"] == 0.92
    assert data["needs_confirmation"] is True
    assert data["requires_user_confirmation"] is True
    assert data["identified_model"]["manufacturer"] == "Dell"
    assert data["identified_model"]["model"] == "Latitude 5420"
    assert len(data["supported_models"]) >= 3


def test_identify_unknown_unsupported_model_returns_manual_picker(client: TestClient):
    mock_ai_output = ModelIdentificationOutput(
        model_name="unknown",
        confidence=0.2,
        visible_label_text=None,
        visual_clues=["Unidentified silver laptop chassis"],
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("unclear.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is False
    assert data["identified_model"] is None
    assert data["needs_confirmation"] is True
    assert len(data["supported_models"]) >= 3
    assert "select" in data["message"].lower() or "manually" in data["message"].lower()


def test_identify_manual_path_bypasses_gemini(client: TestClient):
    """
    Client sends manual_model or model_id directly without images.
    Gemini should never be invoked.
    """
    with patch.object(gemini_client, "generate_structured") as mock_gemini:
        res = client.post(
            "/api/products/identify",
            json={"manual_model": "Dell Latitude 5420"},
        )
        assert res.status_code == 200
        mock_gemini.assert_not_called()

        data = res.json()
        assert data["is_supported"] is True
        assert data["identified_model"]["manufacturer"] == "Dell"
        assert data["identified_model"]["model"] == "Latitude 5420"
        assert data["needs_confirmation"] is True


def test_identify_manual_path_via_model_id(client: TestClient):
    with patch.object(gemini_client, "generate_structured") as mock_gemini:
        res = client.post(
            "/api/products/identify",
            json={"model_id": "lenovo-thinkpad-t14-gen-1"},
        )
        assert res.status_code == 200
        mock_gemini.assert_not_called()

        data = res.json()
        assert data["is_supported"] is True
        assert data["identified_model"]["manufacturer"] == "Lenovo"
        assert data["needs_confirmation"] is True


def test_identify_gemini_failure_returns_ai_failure(client: TestClient):
    with patch.object(
        gemini_client,
        "generate_structured",
        side_effect=AppError(
            code=ErrorCode.AI_FAILURE.value,
            message="Gemini connection timeout",
            http_status=502,
        ),
    ):
        files = [("images", ("front.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 502
    err = res.json()["error"]
    assert err["code"] == ErrorCode.AI_FAILURE.value


# ============================================================================
# 3. Visible Damage Analysis & Post-filter Tests
# ============================================================================

def test_post_filter_drops_internal_hardware_claims():
    """
    CRITICAL NON-NEGOTIABLE RULE:
    A photo can NEVER prove internal battery/SSD/RAM/motherboard health.
    Any finding asserting internal condition must be dropped.
    Visible exterior swelling deforming chassis is remapped to HINGE_CHASSIS.
    """
    raw_findings = [
        VisibleFinding(
            component=ComponentName.DISPLAY,
            description="Diagonal crack across bottom-right LCD glass.",
            severity="HIGH",
        ),
        VisibleFinding(
            component=ComponentName.KEYBOARD,
            description="Missing F4 keycap.",
            severity="MODERATE",
        ),
        VisibleFinding(
            component=ComponentName.BATTERY,
            description="Battery capacity degraded to 65% health.",
            severity="HIGH",
        ),
        VisibleFinding(
            component=ComponentName.SSD,
            description="SSD remaining endurance is 88%.",
            severity="LOW",
        ),
        VisibleFinding(
            component=ComponentName.RAM,
            description="RAM module memory passes diagnostics.",
            severity="LOW",
        ),
        VisibleFinding(
            component="MOTHERBOARD",
            description="Motherboard power rail short circuit.",
            severity="HIGH",
        ),
        VisibleFinding(
            component=ComponentName.HINGE_CHASSIS,
            description="Bottom cover shows visible battery swelling bulging outwards.",
            severity="HIGH",
        ),
    ]

    filtered = filter_visible_findings(raw_findings)

    components = [str(getattr(f.component, "value", f.component)) for f in filtered]
    assert "DISPLAY" in components
    assert "KEYBOARD" in components
    assert "HINGE_CHASSIS" in components
    assert "BATTERY" not in components
    assert "SSD" not in components
    assert "RAM" not in components
    assert "MOTHERBOARD" not in components

    # Ensure internal capacity / endurance / circuit health were discarded
    descriptions = " ".join(f.description.lower() for f in filtered)
    assert "battery capacity degraded" not in descriptions
    assert "ssd remaining endurance" not in descriptions
    assert "memory passes diagnostics" not in descriptions
    assert "motherboard power rail" not in descriptions

    # Exterior swelling is retained under HINGE_CHASSIS
    assert any("bulging" in f.description.lower() for f in filtered)


def test_analyze_with_mocked_gemini_persists_visual_evidence(client: TestClient, registered_product):
    mock_damage = DamageAssessmentOutput(
        cracks=["Hairline crack on top display bezel"],
        dents=["Corner scuff on bottom left chassis"],
        missing_keys=["Caps lock keycap missing"],
        hinge_damage=[],
        port_damage=["Slight dust in USB-A port"],
        visible_swelling=[],
        observations=[
            "Chassis in fair condition",
            "Internal battery health estimate 75%",  # Must be stripped by post-filter!
            "SSD SMART health 95%",                 # Must be stripped by post-filter!
        ],
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_damage):
        files = [
            ("images", ("chassis.jpg", BytesIO(VALID_JPEG), "image/jpeg")),
        ]
        res = client.post(
            "/api/vision/analyze",
            data={"product_id": registered_product.id, "inspection_notes": "Scratches on lid"},
            files=files,
        )

    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == registered_product.id
    assert len(data["findings"]) > 0

    # Verify all findings are strictly VISUAL and exterior
    for f in data["findings"]:
        assert f["evidence_type"] == EvidenceType.VISUAL.value
        assert f["component"] in ["DISPLAY", "KEYBOARD", "HINGE_CHASSIS", "PORTS", "CHASSIS"]
        desc_lower = f["description"].lower()
        assert "battery health" not in desc_lower
        assert "ssd smart" not in desc_lower

    # Verify VISUAL Evidence records were saved to store
    evidence_list = store.get_evidence(registered_product.id)
    visual_evidence = [e for e in evidence_list if e.type == EvidenceType.VISUAL]
    assert len(visual_evidence) == len(data["findings"])
    for ev in visual_evidence:
        assert ev.product_id == registered_product.id
        assert ev.type == EvidenceType.VISUAL
        assert ev.value["observation"]


def test_analyze_gemini_failure_returns_ai_failure(client: TestClient, registered_product):
    with patch.object(
        gemini_client,
        "generate_structured",
        side_effect=AppError(
            code=ErrorCode.AI_FAILURE.value,
            message="Gemini API rate limit exceeded",
            http_status=502,
        ),
    ):
        files = [("images", ("lid.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post(
            "/api/vision/analyze",
            data={"product_id": registered_product.id},
            files=files,
        )

    assert res.status_code == 502
    err = res.json()["error"]
    assert err["code"] == ErrorCode.AI_FAILURE.value


def test_identify_demo_fallback_flag(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", True)
    res = client.post("/api/products/identify", json={"hint": "Lenovo ThinkPad T14 Gen 1"})
    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is True
    assert data["identified_model"]["manufacturer"] == "Lenovo"
    assert any("sample-data" in clue for clue in data["visual_clues"])


def test_analyze_demo_fallback_flag(client: TestClient, registered_product, monkeypatch):
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", True)
    res = client.post(
        "/api/vision/analyze",
        json={"product_id": registered_product.id, "inspection_notes": "dell latitude 5420 keyboard"},
    )
    assert res.status_code == 200
    data = res.json()
    assert len(data["findings"]) > 0
    # Check that saved evidence is labeled source: "sample-data"
    evidence_list = store.get_evidence(registered_product.id)
    sample_ev = [e for e in evidence_list if e.source == "sample-data"]
    assert len(sample_ev) > 0


def test_gemini_failure_fallback_for_demo_model(client: TestClient):
    with patch.object(
        gemini_client,
        "generate_structured",
        side_effect=AppError(
            code=ErrorCode.AI_FAILURE.value,
            message="Gemini connection timeout",
            http_status=502,
        ),
    ):
        files = [("images", ("thinkpad_lid.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", data={"hint": "ThinkPad T14"}, files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is True
    assert data["identified_model"]["manufacturer"] == "Lenovo"
    assert any("sample-data" in clue for clue in data["visual_clues"])
