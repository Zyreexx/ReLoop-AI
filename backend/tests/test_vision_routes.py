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
from app.ai.schemas import CatalogIdentificationOutput, DamageAssessmentOutput
from app.config import settings
from app.db.store import store
from app.errors import AppError, ErrorCode
from app.knowledge.models_catalog import get_catalog_candidates_with_ids, get_candidate_by_id
from app.schemas.enums import ComponentName, ConfidenceLevel, EvidenceType
from app.schemas.product import ProductCandidate, ProductRecord, ProductSpecs
from app.schemas.vision import VisibleFinding
from app.services.vision import (
    filter_visible_findings,
    evaluate_identification_confidence,
    validate_image_roles,
    _is_model_text_in_labels,
)


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


def test_identify_accepts_up_to_5_images_and_rejects_6(client: TestClient):
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",
        label_evidence=["Latitude 5420"],
        visual_evidence=["Dell emblem"],
        contradictions=[],
        model_confidence=0.92,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        # 5 images should be accepted
        files_5 = [
            ("images", (f"pic{i}.jpg", BytesIO(VALID_JPEG), "image/jpeg"))
            for i in range(5)
        ]
        res_5 = client.post("/api/products/identify", files=files_5)
        assert res_5.status_code == 200
        assert res_5.json()["source"] == "live"

    # 6 images should be rejected
    files_6 = [
        ("images", (f"pic{i}.jpg", BytesIO(VALID_JPEG), "image/jpeg"))
        for i in range(6)
    ]
    res_6 = client.post("/api/products/identify", files=files_6)
    assert res_6.status_code == 400
    err = res_6.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value
    assert "maximum of 5 images" in err["message"].lower()


def test_identify_rejects_empty_file(client: TestClient):
    files = [("images", ("empty.jpg", BytesIO(b""), "image/jpeg"))]
    res = client.post("/api/products/identify", files=files)
    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value


# ============================================================================
# 2. Product Identification & Confidence Policy Tests
# ============================================================================

def test_catalog_candidate_ids_stable_across_runs():
    """Catalog candidate IDs (C1, C2, ...) must be generated deterministically from sorted catalog."""
    first_run = get_catalog_candidates_with_ids()
    second_run = get_catalog_candidates_with_ids()

    assert len(first_run) == len(second_run)
    assert len(first_run) >= 4
    for r1, r2 in zip(first_run, second_run):
        assert r1["candidate_id"] == r2["candidate_id"]
        assert r1["manufacturer"] == r2["manufacturer"]
        assert r1["model"] == r2["model"]

    # Verify expected candidate IDs in alphabetical sort
    c_ids = {c["candidate_id"]: f"{c['manufacturer']} {c['model']}" for c in first_run}
    assert "C1" in c_ids and "Apple" in c_ids["C1"]
    assert "C2" in c_ids and "Dell" in c_ids["C2"]
    assert "C3" in c_ids and "HP" in c_ids["C3"]
    assert "C4" in c_ids and "Lenovo" in c_ids["C4"]


def test_identify_exact_label_match_evaluates_to_high(client: TestClient):
    """Exact model text in label_evidence -> HIGH confidence."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",
        label_evidence=["Dell Latitude 5420 Regulatory Model P137G"],
        visual_evidence=["Silver chassis finish"],
        contradictions=[],
        model_confidence=0.88,
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
    assert data["candidate_id"] == "C2"
    assert data["confidence_level"] == ConfidenceLevel.HIGH.value
    assert data["identified_model"]["manufacturer"] == "Dell"
    assert data["identified_model"]["model"] == "Latitude 5420"
    assert data["needs_confirmation"] is True
    assert data["source"] == "live"
    assert len(data["label_evidence"]) >= 1


def test_identify_distinct_visual_clues_without_contradiction_evaluates_to_medium(client: TestClient):
    """Visual-only evidence (even >= 3 items) caps at MEDIUM confidence (HIGH requires specific model text in labels)."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",
        label_evidence=[],
        visual_evidence=[
            "Circular Dell logo centered on top lid",
            "Left-side dual Thunderbolt USB-C ports",
            "Right-side RJ-45 Ethernet drop-jaw port",
        ],
        contradictions=[],
        model_confidence=0.7,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("chassis.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == "C2"
    assert data["confidence_level"] == ConfidenceLevel.MEDIUM.value


def test_identify_brand_only_evaluates_to_medium(client: TestClient):
    """Manufacturer clear but exact model not confirmed by label text -> MEDIUM."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",
        label_evidence=["Dell circular logo badge"],
        visual_evidence=["Silver matte finish"],
        contradictions=[],
        model_confidence=0.85,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("lid.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == "C2"
    assert data["confidence_level"] == ConfidenceLevel.MEDIUM.value
    assert data["needs_confirmation"] is True


def test_identify_generic_look_evaluates_to_low(client: TestClient):
    """Only generic visual similarity -> LOW."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",
        label_evidence=[],
        visual_evidence=["Dark gray laptop chassis"],
        contradictions=[],
        model_confidence=0.5,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("device.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["candidate_id"] == "C2"
    assert data["confidence_level"] == ConfidenceLevel.LOW.value
    assert data["needs_confirmation"] is True


def test_identify_unknown_candidate_returns_manual_picker(client: TestClient):
    """Gemini selects UNKNOWN -> returns manual picker with supported model catalog."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="UNKNOWN",
        label_evidence=[],
        visual_evidence=["Blurry image of electronic device"],
        contradictions=["Unable to determine make or model"],
        model_confidence=0.1,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("unclear.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is False
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["confidence_level"] == ConfidenceLevel.UNKNOWN.value
    assert data["needs_confirmation"] is True
    assert len(data["supported_models"]) >= 4


def test_identify_candidate_not_in_catalog_downgrades_to_unknown(client: TestClient):
    """Candidate ID not in catalog (e.g. C99) -> downgraded to UNKNOWN manual picker."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C99",
        label_evidence=["Alienware m15 R7"],
        visual_evidence=["Alien head logo"],
        contradictions=[],
        model_confidence=0.9,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("gaming.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is False
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["confidence_level"] == ConfidenceLevel.UNKNOWN.value


def test_identify_contradiction_downgrades_to_unknown(client: TestClient):
    """Response contradiction (e.g. chosen candidate Dell C2 but label reads Lenovo) -> downgraded to UNKNOWN."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",  # Dell Latitude 5420
        label_evidence=["Lenovo ThinkPad T14 Gen 1 label"],
        visual_evidence=["Red TrackPoint nub visible"],
        contradictions=["Selected candidate is Dell but chassis shows Lenovo ThinkPad branding"],
        model_confidence=0.9,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("thinkpad.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["is_supported"] is False
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["confidence_level"] == ConfidenceLevel.UNKNOWN.value


def test_identify_high_numeric_confidence_with_no_evidence_not_high(client: TestClient):
    """Gemini reports 0.99 confidence with no evidence -> policy refuses to evaluate as HIGH."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",
        label_evidence=[],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.99,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("blank.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    # With 0 label evidence and 0 visual evidence, confidence level must not be HIGH
    assert data["confidence_level"] != ConfidenceLevel.HIGH.value
    assert data["confidence_level"] == ConfidenceLevel.UNKNOWN.value


def test_identify_image_roles_matching_passes_to_service(client: TestClient):
    """Valid image_roles matching image count is accepted."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="C2",
        label_evidence=["Latitude 5420"],
        visual_evidence=["Chassis overall view", "Bottom asset tag"],
        contradictions=[],
        model_confidence=0.95,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output) as mock_gemini:
        files = [
            ("images", ("front.jpg", BytesIO(VALID_JPEG), "image/jpeg")),
            ("images", ("bottom.png", BytesIO(VALID_PNG), "image/png")),
        ]
        data = {"image_roles": '["overall", "bottom_label"]'}
        res = client.post("/api/products/identify", data=data, files=files)

        assert res.status_code == 200
        assert mock_gemini.called
        call_prompt = mock_gemini.call_args[1]["prompt"]
        assert "IMAGE 1 = overall" in call_prompt
        assert "IMAGE 2 = bottom_label" in call_prompt


def test_identify_image_roles_length_mismatch_returns_invalid_input(client: TestClient):
    """Mismatched image_roles list length returns typed INVALID_INPUT error."""
    files = [
        ("images", ("front.jpg", BytesIO(VALID_JPEG), "image/jpeg")),
        ("images", ("bottom.png", BytesIO(VALID_PNG), "image/png")),
    ]
    # 2 images but 1 role
    data = {"image_roles": '["overall"]'}
    res = client.post("/api/products/identify", data=data, files=files)

    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value
    assert "image_roles length" in err["message"]


def test_identify_image_roles_invalid_role_returns_invalid_input(client: TestClient):
    """Unrecognized image role returns typed INVALID_INPUT error."""
    files = [("images", ("front.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
    data = {"image_roles": '["space_shuttle"]'}
    res = client.post("/api/products/identify", data=data, files=files)

    assert res.status_code == 400
    err = res.json()["error"]
    assert err["code"] == ErrorCode.INVALID_INPUT.value
    assert "Invalid image role" in err["message"]


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
        assert data["candidate_id"] == "C2"
        assert data["confidence_level"] == ConfidenceLevel.HIGH.value
        assert data["needs_confirmation"] is True
        assert data["source"] == "manual"


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
        assert data["candidate_id"] == "C4"
        assert data["needs_confirmation"] is True
        assert data["source"] == "manual"


def test_identify_gemini_failure_returns_ai_unavailable(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
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

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AI_UNAVAILABLE"
    assert data["is_supported"] is False
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert "temporarily unavailable" in data["message"].lower()


def test_evaluate_identification_confidence_unit_matrix():
    """Direct unit testing of confidence policy function across all requirement tiers."""
    cand = ProductCandidate(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )

    # 1. Exact model label match -> HIGH
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="C2",
        label_evidence=["Latitude 5420 regulatory text"],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.5,
    )
    assert conf == ConfidenceLevel.HIGH

    # 2. 3 visual items, no contradictions -> MEDIUM (visual-only evidence caps at MEDIUM)
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="C2",
        label_evidence=[],
        visual_evidence=["Silver chassis", "Wedge lock slot", "Round logo"],
        contradictions=[],
        model_confidence=0.1,
    )
    assert conf == ConfidenceLevel.MEDIUM

    # 3. Brand only in label -> MEDIUM
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="C2",
        label_evidence=["Dell"],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.99,
    )
    assert conf == ConfidenceLevel.MEDIUM

    # 4. Generic look (1 item) -> LOW
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="C2",
        label_evidence=[],
        visual_evidence=["Black laptop edge"],
        contradictions=[],
        model_confidence=0.99,
    )
    assert conf == ConfidenceLevel.LOW

    # 5. UNKNOWN candidate ID -> UNKNOWN
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="UNKNOWN",
        label_evidence=["Latitude 5420"],
        visual_evidence=["Silver chassis"],
        contradictions=[],
        model_confidence=0.99,
    )
    assert conf == ConfidenceLevel.UNKNOWN

    # 6. None candidate -> UNKNOWN
    conf = evaluate_identification_confidence(
        candidate=None,
        candidate_id="C2",
        label_evidence=["Latitude 5420"],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.99,
    )
    assert conf == ConfidenceLevel.UNKNOWN

    # 7. Contradiction in label -> UNKNOWN
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="C2",
        label_evidence=["Lenovo ThinkPad T14"],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.99,
    )
    assert conf == ConfidenceLevel.UNKNOWN

    # 8. Contradiction in contradictions list -> UNKNOWN
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="C2",
        label_evidence=["Latitude 5420"],
        visual_evidence=[],
        contradictions=["Ports do not match Dell chassis"],
        model_confidence=0.99,
    )
    assert conf == ConfidenceLevel.UNKNOWN

    # 9. No evidence -> UNKNOWN even if model_confidence=0.99
    conf = evaluate_identification_confidence(
        candidate=cand,
        candidate_id="C2",
        label_evidence=[],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.99,
    )
    assert conf == ConfidenceLevel.UNKNOWN


def test_vision_confidence_family_name_alone_does_not_qualify_high():
    """
    Tests that pure family/series names (Latitude, ThinkPad, EliteBook, MacBook) alone
    never qualify as HIGH confidence without specific model numbers.
    """
    dell_cand = ProductCandidate(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )
    lenovo_cand = ProductCandidate(
        manufacturer="Lenovo",
        model="ThinkPad T14 Gen 1",
        model_year=2020,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )
    hp_cand = ProductCandidate(
        manufacturer="HP",
        model="EliteBook 840 G7",
        model_year=2020,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )
    apple_cand = ProductCandidate(
        manufacturer="Apple",
        model="MacBook Air (M1, 2020)",
        model_year=2020,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )

    # 1. Family name alone -> _is_model_text_in_labels is False, confidence is MEDIUM (not HIGH)
    assert not _is_model_text_in_labels(dell_cand, ["Latitude"])
    conf_dell = evaluate_identification_confidence(
        candidate=dell_cand,
        candidate_id="C2",
        label_evidence=["Latitude"],
        visual_evidence=[],
        contradictions=[],
    )
    assert conf_dell != ConfidenceLevel.HIGH
    assert conf_dell == ConfidenceLevel.MEDIUM

    assert not _is_model_text_in_labels(lenovo_cand, ["ThinkPad"])
    conf_lenovo = evaluate_identification_confidence(
        candidate=lenovo_cand,
        candidate_id="C4",
        label_evidence=["ThinkPad"],
        visual_evidence=[],
        contradictions=[],
    )
    assert conf_lenovo != ConfidenceLevel.HIGH
    assert conf_lenovo == ConfidenceLevel.MEDIUM

    assert not _is_model_text_in_labels(hp_cand, ["EliteBook"])
    conf_hp = evaluate_identification_confidence(
        candidate=hp_cand,
        candidate_id="C3",
        label_evidence=["EliteBook"],
        visual_evidence=[],
        contradictions=[],
    )
    assert conf_hp != ConfidenceLevel.HIGH
    assert conf_hp == ConfidenceLevel.MEDIUM

    assert not _is_model_text_in_labels(apple_cand, ["MacBook"])
    assert not _is_model_text_in_labels(apple_cand, ["MacBook Air"])
    conf_apple = evaluate_identification_confidence(
        candidate=apple_cand,
        candidate_id="C1",
        label_evidence=["MacBook Air"],
        visual_evidence=[],
        contradictions=[],
    )
    assert conf_apple != ConfidenceLevel.HIGH
    assert conf_apple == ConfidenceLevel.MEDIUM

    # 2. Full model name -> _is_model_text_in_labels is True, confidence is HIGH
    assert _is_model_text_in_labels(dell_cand, ["Latitude 5420"])
    assert _is_model_text_in_labels(dell_cand, ["Dell Latitude 5420"])
    conf_full = evaluate_identification_confidence(
        candidate=dell_cand,
        candidate_id="C2",
        label_evidence=["Latitude 5420"],
    )
    assert conf_full == ConfidenceLevel.HIGH

    # 3. Specific model number alone -> _is_model_text_in_labels is True, confidence is HIGH
    assert _is_model_text_in_labels(dell_cand, ["5420"])
    conf_num = evaluate_identification_confidence(
        candidate=dell_cand,
        candidate_id="C2",
        label_evidence=["5420"],
    )
    assert conf_num == ConfidenceLevel.HIGH

    # 4. M1 digit-bearing token for MacBook Air (M1, 2020) -> True and HIGH
    # 'M1' contains the digit '1' and is an unambiguous specific silicon/model identifier
    assert _is_model_text_in_labels(apple_cand, ["M1"])
    conf_m1 = evaluate_identification_confidence(
        candidate=apple_cand,
        candidate_id="C1",
        label_evidence=["M1"],
    )
    assert conf_m1 == ConfidenceLevel.HIGH


def test_ambiguity_guard_with_synthetic_candidates():
    """
    Tests that digit-bearing identifiers that overlap or conflict across candidates
    are rejected by the ambiguity guard to prevent false HIGH confidence.
    """
    cand_a = ProductCandidate(
        manufacturer="Acme",
        model="Pro 14",
        model_year=2021,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )
    cand_b = ProductCandidate(
        manufacturer="Acme",
        model="Pro 140",
        model_year=2021,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )
    synthetic_catalog = [cand_a, cand_b]

    # '14' is a substring of '140' -> Ambiguous! Neither bare number qualifies for HIGH
    assert not _is_model_text_in_labels(cand_a, ["14"], catalog_candidates=synthetic_catalog)
    assert not _is_model_text_in_labels(cand_b, ["140"], catalog_candidates=synthetic_catalog)

    conf_a = evaluate_identification_confidence(
        candidate=cand_a,
        candidate_id="C1",
        label_evidence=["14"],
        catalog_candidates=synthetic_catalog,
    )
    assert conf_a != ConfidenceLevel.HIGH

    conf_b = evaluate_identification_confidence(
        candidate=cand_b,
        candidate_id="C2",
        label_evidence=["140"],
        catalog_candidates=synthetic_catalog,
    )
    assert conf_b != ConfidenceLevel.HIGH

    # Exact full model strings still pass and achieve HIGH
    assert _is_model_text_in_labels(cand_a, ["Pro 14"], catalog_candidates=synthetic_catalog)
    assert _is_model_text_in_labels(cand_b, ["Pro 140"], catalog_candidates=synthetic_catalog)


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
    assert data["source"] == "live"
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
    assert data["source"] == "sample-data"
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
    assert data["source"] == "sample-data"
    assert len(data["findings"]) > 0
    # Check that saved evidence is labeled source: "sample-data"
    evidence_list = store.get_evidence(registered_product.id)
    sample_ev = [e for e in evidence_list if e.source == "sample-data"]
    assert len(sample_ev) > 0


def test_gemini_failure_fallback_for_demo_model(client: TestClient, monkeypatch):
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", True)
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
    assert data["status"] == "IDENTIFIED"
    assert data["is_supported"] is True
    assert data["source"] == "sample-data"
    assert data["identified_model"]["manufacturer"] == "Lenovo"
    assert any("sample-data" in clue for clue in data["visual_clues"])


# ============================================================================
# Task 8 Regression & Safety Tests
# ============================================================================

def test_gemini_429_quota_returns_ai_unavailable_never_dell(client: TestClient, monkeypatch):
    """Rule 4: Gemini 429 quota exceeded returns AI_UNAVAILABLE, never Dell."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
    with patch.object(
        gemini_client,
        "generate_structured",
        side_effect=AppError(
            code=ErrorCode.AI_FAILURE.value,
            message="Resource has been exhausted (e.g. check quota)",
            http_status=429,
        ),
    ):
        files = [("images", ("laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AI_UNAVAILABLE"
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["is_supported"] is False


def test_gemini_503_unavailable_returns_ai_unavailable_never_dell(client: TestClient, monkeypatch):
    """Rule 4: Gemini 503 unavailable returns AI_UNAVAILABLE, never Dell."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
    with patch.object(
        gemini_client,
        "generate_structured",
        side_effect=AppError(
            code=ErrorCode.AI_FAILURE.value,
            message="The service is temporarily unavailable",
            http_status=503,
        ),
    ):
        files = [("images", ("laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AI_UNAVAILABLE"
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["is_supported"] is False


def test_gemini_timeout_network_failure_returns_ai_unavailable(client: TestClient, monkeypatch):
    """Rule 4: Gemini network timeout returns AI_UNAVAILABLE."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
    with patch.object(
        gemini_client,
        "generate_structured",
        side_effect=Exception("ReadTimeout: HTTPSConnectionPool(host='generativelanguage.googleapis.com')"),
    ):
        files = [("images", ("laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AI_UNAVAILABLE"
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["is_supported"] is False


def test_filename_victus_never_identifies_dell(client: TestClient, monkeypatch):
    """Rule 5: Filenames containing 'victus' must NOT identify Dell Latitude 5420."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="UNKNOWN",
        label_evidence=["HP Victus 15 gaming logo"],
        visual_evidence=["V-shaped logo on lid"],
        contradictions=[],
        model_confidence=0.9,
    )
    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("HP_Victus.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", data={"hint": "HP_Victus.jpg"}, files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UNKNOWN"
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["is_supported"] is False


def test_filename_loq_never_identifies_dell_or_supported_model(client: TestClient, monkeypatch):
    """Rule 5: Filenames containing 'loq' must NOT identify Dell or any supported model automatically."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="UNKNOWN",
        label_evidence=["Lenovo LOQ 15IRH8"],
        visual_evidence=["LOQ badge on lid corner"],
        contradictions=[],
        model_confidence=0.9,
    )
    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("Lenovo_LOQ.png", BytesIO(VALID_PNG), "image/png"))]
        res = client.post("/api/products/identify", data={"hint": "loq1.jpg"}, files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UNKNOWN"
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["is_supported"] is False


def test_gemini_returns_unknown_gives_unknown_status(client: TestClient):
    """Rule 2: Gemini returns UNKNOWN -> response status is UNKNOWN."""
    mock_ai_output = CatalogIdentificationOutput(
        candidate_id="UNKNOWN",
        label_evidence=[],
        visual_evidence=["Unclear dark chassis"],
        contradictions=[],
        model_confidence=0.4,
    )
    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("blurry.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "UNKNOWN"
    assert data["identified_model"] is None
    assert data["candidate_id"] == "UNKNOWN"
    assert data["is_supported"] is False


def test_demo_fallback_false_on_gemini_failure_never_returns_sample_data(client: TestClient, monkeypatch):
    """Rule 6: When DEMO_FALLBACK=false, Gemini failure returns AI_UNAVAILABLE, never sample data."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", False)
    with patch.object(
        gemini_client,
        "generate_structured",
        side_effect=Exception("API Error"),
    ):
        files = [("images", ("test.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", data={"hint": "Dell Latitude 5420"}, files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "AI_UNAVAILABLE"
    assert data["source"] != "sample-data"
    assert data["identified_model"] is None


def test_demo_fallback_true_for_unsupported_hint_returns_unknown(client: TestClient, monkeypatch):
    """Rule 6: When DEMO_FALLBACK=true, unsupported models like Victus or LOQ return UNKNOWN, not Dell."""
    monkeypatch.setattr("app.config.settings.DEMO_FALLBACK", True)
    res_victus = client.post("/api/products/identify", json={"hint": "HP Victus 15"})
    assert res_victus.status_code == 200
    data_victus = res_victus.json()
    assert data_victus["status"] == "UNKNOWN"
    assert data_victus["identified_model"] is None

    res_loq = client.post("/api/products/identify", json={"hint": "Lenovo LOQ 15"})
    assert res_loq.status_code == 200
    data_loq = res_loq.json()
    assert data_loq["status"] == "UNKNOWN"
    assert data_loq["identified_model"] is None


# ============================================================================
# 8. Open-Ended Laptop Vision Identification Tests
# ============================================================================

def test_identify_non_catalog_laptop_with_specific_label_evaluates_to_high(client: TestClient):
    """Laptops not in the 4-model catalog identify successfully with HIGH confidence when specific model label is present."""
    mock_ai_output = CatalogIdentificationOutput(
        manufacturer="Acer",
        model="Aspire 5 A515-56",
        model_year=2021,
        label_evidence=["Acer Aspire 5 Model A515-56-50RS"],
        visual_evidence=["Silver sandblasted aluminum top cover", "Elevated hinge design"],
        contradictions=[],
        model_confidence=0.95,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("acer_bottom.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IDENTIFIED"
    assert data["confidence_level"] == ConfidenceLevel.HIGH.value
    assert data["identified_model"]["manufacturer"] == "Acer"
    assert data["identified_model"]["model"] == "Aspire 5 A515-56"
    assert data["identified_model"]["model_year"] == 2021


def test_identify_non_catalog_laptop_bare_family_name_alone_is_not_high(client: TestClient):
    """Bare family name like 'Aspire' alone without model number designator evaluates to MEDIUM, not HIGH."""
    mock_ai_output = CatalogIdentificationOutput(
        manufacturer="Acer",
        model="Aspire 5 A515-56",
        model_year=2021,
        label_evidence=["Acer Aspire"],
        visual_evidence=["Silver chassis", "Acer logo"],
        contradictions=[],
        model_confidence=0.88,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("acer_lid.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IDENTIFIED"
    assert data["confidence_level"] == ConfidenceLevel.MEDIUM.value
    assert data["identified_model"]["manufacturer"] == "Acer"
    assert data["identified_model"]["model"] == "Aspire 5 A515-56"


def test_identify_non_catalog_asus_zenbook_visual_only_caps_at_medium(client: TestClient):
    """Non-catalog ASUS ZenBook identified via visual clues caps at MEDIUM confidence."""
    mock_ai_output = CatalogIdentificationOutput(
        manufacturer="ASUS",
        model="ZenBook 14 UX425",
        model_year=2020,
        label_evidence=[],
        visual_evidence=["Spun-metal concentric circle finish on lid", "ErgoLift hinge", "NumberPad 2.0 in touchpad"],
        contradictions=[],
        model_confidence=0.85,
    )

    with patch.object(gemini_client, "generate_structured", return_value=mock_ai_output):
        files = [("images", ("asus_zenbook.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "IDENTIFIED"
    assert data["confidence_level"] == ConfidenceLevel.MEDIUM.value
    assert data["identified_model"]["manufacturer"] == "ASUS"
    assert data["identified_model"]["model"] == "ZenBook 14 UX425"


def test_identify_open_ended_with_ambiguous_bare_number_in_isolation():
    """An ambiguous digit in isolation without brand context does not evaluate to HIGH confidence."""
    cand = ProductCandidate(
        manufacturer="GenericBrand",
        model="Model 15",
        model_year=2022,
        confidence=ConfidenceLevel.HIGH,
        specs=ProductSpecs(),
    )

    # Label only has bare '15' without brand context
    conf = evaluate_identification_confidence(
        candidate=cand,
        label_evidence=["15"],
        visual_evidence=[],
        contradictions=[],
        model_confidence=0.9,
    )
    assert conf != ConfidenceLevel.HIGH

