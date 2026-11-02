"""
Automated tests for laptop image identification reliability and non-laptop rejection guard.

Requirements covered:
1. Smartphone image -> NON_LAPTOP_REJECTED, allow_manual_selection=False, is_laptop=False.
2. Monitor image -> NON_LAPTOP_REJECTED, allow_manual_selection=False, is_laptop=False.
3. Tablet image -> NON_LAPTOP_REJECTED, allow_manual_selection=False, is_laptop=False.
4. Logo-less laptop -> NOT rejected; handled as genuine laptop (UNKNOWN or IDENTIFIED), allow_manual_selection=True.
5. Blurry laptop image -> Handled cautiously as UNKNOWN rather than classified as non-laptop; allow_manual_selection=True.
6. Ambiguous image -> Handled cautiously as UNKNOWN rather than classified as non-laptop; allow_manual_selection=True.
7. Confirmed non-laptop result attempting to proceed into laptop assessment -> Rejected at all backend layers (identify, product create, assessment build, vision analyze).
8. Genuine but unidentified laptop retaining the manual-selection option -> status=UNKNOWN, allow_manual_selection=True, supported_models populated, manual model override succeeds.
"""
from io import BytesIO
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from app.ai.gemini_client import gemini_client
from app.ai.schemas import OpenIdentificationOutput
from app.errors import AppError, ErrorCode
from app.schemas.enums import ConfidenceLevel, DeviceCategory, IdentificationStatus
from app.schemas.product import ProductCreate

VALID_JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00" + b"\x00" * 30


# 1. Smartphone image rejection
def test_01_smartphone_image_rejected(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="Apple",
        model="iPhone 14 Pro",
        model_year=2022,
        label_evidence=[],
        visual_evidence=["Mobile smartphone with triple rear camera array, notch display"],
        contradictions=["Non-laptop handheld mobile device"],
        model_confidence=0.95,
        is_laptop=False,
        detected_device_type="SMARTPHONE",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("phone.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.NON_LAPTOP_REJECTED.value
    assert data["is_laptop"] is False
    assert data["allow_manual_selection"] is False
    assert data["identified_model"] is None
    assert len(data.get("supported_models", [])) == 0
    assert "smartphone" in data["message"].lower() or "laptop" in data["message"].lower()


# 2. Monitor image rejection
def test_02_monitor_image_rejected(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="Dell",
        model="UltraSharp 27 Monitor",
        model_year=2021,
        label_evidence=["Dell UltraSharp U2720Q Label"],
        visual_evidence=["Standalone desktop computer monitor with desk stand and bezels, no integrated keyboard or battery"],
        contradictions=["Standalone display panel without laptop body"],
        model_confidence=0.90,
        is_laptop=False,
        detected_device_type="MONITOR",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("monitor.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.NON_LAPTOP_REJECTED.value
    assert data["is_laptop"] is False
    assert data["allow_manual_selection"] is False
    assert data["identified_model"] is None
    assert "monitor" in data["message"].lower()


# 3. Tablet image rejection
def test_03_tablet_image_rejected(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="Apple",
        model="iPad Air",
        model_year=2022,
        label_evidence=["iPad Regulatory Model A2588"],
        visual_evidence=["Slate touchscreen tablet without attached physical laptop keyboard base"],
        contradictions=["Tablet slate device"],
        model_confidence=0.92,
        is_laptop=False,
        detected_device_type="TABLET",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("tablet.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.NON_LAPTOP_REJECTED.value
    assert data["is_laptop"] is False
    assert data["allow_manual_selection"] is False
    assert data["identified_model"] is None
    assert "tablet" in data["message"].lower()


# 4. Logo-less laptop is not rejected
def test_04_logo_less_laptop_not_rejected(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="UNKNOWN",
        model="UNKNOWN",
        model_year=None,
        label_evidence=[],
        visual_evidence=["Clamshell form factor laptop with physical keyboard, touchpad, display hinge, and side USB-C ports", "No visible manufacturer logo or badge on chassis lid"],
        contradictions=[],
        model_confidence=0.60,
        is_laptop=True,
        detected_device_type="LAPTOP",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("unbranded_laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.UNKNOWN.value
    assert data["is_laptop"] is True
    assert data["allow_manual_selection"] is True
    assert len(data["supported_models"]) > 0
    assert "select your model manually" in data["message"].lower()


# 5. Blurry laptop image handled cautiously as UNKNOWN
def test_05_blurry_laptop_handled_cautiously(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="UNKNOWN",
        model="UNKNOWN",
        model_year=None,
        label_evidence=[],
        visual_evidence=["Blurry image showing dark clamshell device with keyboard silhouette", "Severe motion blur prevents fine model label reading"],
        contradictions=[],
        model_confidence=0.35,
        is_laptop=True,
        detected_device_type="LAPTOP",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("blurry_laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    # Must NOT be classified as NON_LAPTOP_REJECTED
    assert data["status"] == IdentificationStatus.UNKNOWN.value
    assert data["is_laptop"] is True
    assert data["allow_manual_selection"] is True


# 6. Ambiguous image handled cautiously as UNKNOWN
def test_06_ambiguous_image_handled_cautiously(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="UNKNOWN",
        model="UNKNOWN",
        model_year=None,
        label_evidence=[],
        visual_evidence=["Ambiguous metallic corner with rubber foot, partial vent slot visible"],
        contradictions=[],
        model_confidence=0.30,
        is_laptop=True,
        detected_device_type="LAPTOP",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("ambiguous.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.UNKNOWN.value
    assert data["is_laptop"] is True
    assert data["allow_manual_selection"] is True


# 7. Confirmed non-laptop attempting to proceed into laptop assessment is rejected
def test_07_confirmed_non_laptop_proceeding_is_blocked(client: TestClient):
    # 7a. Manual identify attempt with non-laptop name
    res = client.post("/api/products/identify", data={"manual_model": "Apple iPhone 14 Pro"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == IdentificationStatus.NON_LAPTOP_REJECTED.value
    assert data["allow_manual_selection"] is False
    assert data["is_laptop"] is False

    # 7b. Product creation with non-laptop category blocked
    res_cat = client.post(
        "/api/products",
        json={"manufacturer": "Samsung", "model": "Galaxy S23", "model_year": 2023, "category": "SMARTPHONE"},
    )
    assert res_cat.status_code == 400
    assert "only evaluates laptop computers" in res_cat.json()["error"]["message"]

    # 7c. Product creation with non-laptop model name blocked even if category is LAPTOP
    res_mod = client.post(
        "/api/products",
        json={"manufacturer": "Dell", "model": "UltraSharp 27 Monitor", "model_year": 2021, "category": "LAPTOP"},
    )
    assert res_mod.status_code == 400
    assert "Confirmed non-laptop device" in res_mod.json()["error"]["message"]

    # 7d. Assessment build on a non-laptop device blocked
    # First, simulate a database product record that had non-laptop category
    from app.db.store import store
    from app.schemas.product import ProductRecord
    fake_phone_record = ProductRecord(
        id="prod_fake_phone_999",
        manufacturer="Apple",
        model="iPhone 13",
        model_year=2021,
        category="SMARTPHONE",
    )
    store.save_product(fake_phone_record)

    build_res = client.post("/api/assessment/build", json={"product_id": "prod_fake_phone_999"})
    assert build_res.status_code == 400
    assert "only supports laptops" in build_res.json()["error"]["message"]

    # 7e. Vision analyze on a non-laptop device blocked
    analyze_res = client.post(
        "/api/vision/analyze",
        data={"product_id": "prod_fake_phone_999"},
        files=[("images", ("phone.jpg", BytesIO(VALID_JPEG), "image/jpeg"))],
    )
    assert analyze_res.status_code == 400
    assert "Product is not a laptop" in analyze_res.json()["error"]["message"]


# 8. Genuine unidentified laptop retains manual-selection option and can proceed
def test_08_genuine_unidentified_laptop_retains_manual_selection(client: TestClient):
    ai_output = OpenIdentificationOutput(
        manufacturer="UNKNOWN",
        model="UNKNOWN",
        model_year=None,
        label_evidence=[],
        visual_evidence=["Silver laptop chassis with keyboard, touchpad, and display hinge", "Brand markings worn and unreadable"],
        contradictions=[],
        model_confidence=0.50,
        is_laptop=True,
        detected_device_type="LAPTOP",
    )
    with patch.object(gemini_client, "generate_structured", return_value=ai_output):
        files = [("images", ("unidentified_laptop.jpg", BytesIO(VALID_JPEG), "image/jpeg"))]
        res = client.post("/api/products/identify", files=files)

    assert res.status_code == 200
    data = res.json()
    # Unidentified/unsupported in catalog returns UNKNOWN with manual selection enabled
    assert data["status"] == IdentificationStatus.UNKNOWN.value
    assert data["allow_manual_selection"] is True
    assert data["is_laptop"] is True
    assert len(data["supported_models"]) > 0

    # User can select a supported catalog model (e.g. Dell Latitude 5420) and register it
    reg_res = client.post(
        "/api/products",
        json={"manufacturer": "Dell", "model": "Latitude 5420", "model_year": 2021, "category": "LAPTOP"},
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["manufacturer"] == "Dell"
    assert reg_data["model"] == "Latitude 5420"
