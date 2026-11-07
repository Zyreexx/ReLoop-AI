"""
Tests for Digital Product Passport (DPP) Service & API.
Validates CIRPASS / ESPR compliance, cryptographic verification hashes,
QR code generation, privacy redactions, and JSON export.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.store import store
from app.schemas.enums import DeviceCategory
from app.schemas.product import ProductRecord, ProductSpecs

client = TestClient(app)


@pytest.fixture
def sample_laptop_for_dpp():
    prod_id = "test_dpp_laptop_001"
    product = ProductRecord(
        id=prod_id,
        manufacturer="Lenovo",
        model="ThinkPad T14 Gen 1",
        model_year=2021,
        age=3.5,
        category=DeviceCategory.LAPTOP,
        serial_or_identifier="PF2X9901",
        specs=ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=True,
            ssd_modular=True,
            battery_replaceable=True,
            display_size_inches=14.0,
            weight_kg=1.5,
        ),
    )
    store.save_product(product)
    return prod_id


def test_generate_dpp_and_schema_validation(sample_laptop_for_dpp):
    prod_id = sample_laptop_for_dpp
    resp = client.post(f"/api/dpp/{prod_id}/generate")
    assert resp.status_code == 200
    dpp = resp.json()

    # Schema validation
    assert dpp["schema_version"] == "CIRPASS-ESPR-v1.0"
    assert dpp["dpp_id"].startswith("urn:dpp:eu:reloop:")
    assert dpp["verification_status"] == "VERIFIED"
    assert len(dpp["verification_hash"]) == 64  # SHA-256

    # Product Identification
    prod_ident = dpp["product_identification"]
    assert prod_ident["manufacturer"] == "Lenovo"
    assert prod_ident["model"] == "ThinkPad T14 Gen 1"
    assert prod_ident["model_year"] == 2021

    # Repairability & Sustainability
    rep = dpp["repairability_and_circularity"]
    assert 0.0 <= rep["repairability_score"] <= 10.0
    assert rep["modularity_rating"] in ["HIGH", "MODERATE", "PROPRIETARY"]
    assert rep["battery_replaceable"] is True

    # QR Code
    assert dpp["qr_code_base64"].startswith("data:image/png;base64,")


def test_get_public_passport_privacy_safeguards(sample_laptop_for_dpp):
    prod_id = sample_laptop_for_dpp
    gen_resp = client.post(f"/api/dpp/{prod_id}/generate")
    dpp_id = gen_resp.json()["dpp_id"]

    # Retrieve public passport
    pub_resp = client.get(f"/api/dpp/{dpp_id}")
    assert pub_resp.status_code == 200
    pub_dpp = pub_resp.json()

    # Check privacy redaction on serial
    serial = pub_dpp["product_identification"]["serial_or_identifier"]
    assert serial.startswith("***-")
    assert serial.endswith("9901")


def test_dpp_qr_code_binary_endpoint(sample_laptop_for_dpp):
    prod_id = sample_laptop_for_dpp
    gen_resp = client.post(f"/api/dpp/{prod_id}/generate")
    dpp_id = gen_resp.json()["dpp_id"]

    qr_resp = client.get(f"/api/dpp/{dpp_id}/qr")
    assert qr_resp.status_code == 200
    assert qr_resp.headers["content-type"] == "image/png"
    # Check PNG magic bytes: \x89PNG\r\n\x1a\n
    assert qr_resp.content[:8] == b"\x89PNG\r\n\x1a\n"


def test_dpp_export_cirpass_json(sample_laptop_for_dpp):
    prod_id = sample_laptop_for_dpp
    gen_resp = client.post(f"/api/dpp/{prod_id}/generate")
    dpp_id = gen_resp.json()["dpp_id"]

    exp_resp = client.get(f"/api/dpp/{dpp_id}/export")
    assert exp_resp.status_code == 200
    assert "application/json" in exp_resp.headers["content-type"]
    exported = exp_resp.json()
    assert exported["schema_version"] == "CIRPASS-ESPR-v1.0"
    assert exported["dpp_id"] == dpp_id
