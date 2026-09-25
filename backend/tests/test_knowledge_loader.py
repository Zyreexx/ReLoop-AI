"""
Tests for structured knowledge loader, product definitions, repair costs,
lifecycle assumptions, and demo case specifications.
"""
import pytest
from app.errors import AppError, ErrorCode, UNSUPPORTED_MODEL
from app.knowledge import (
    get_demo_data_dir,
    get_model_spec,
    get_products_data_dir,
    get_repair_cost,
    get_supported_models,
    get_supported_product_candidates,
    get_useful_life,
    load_all_products,
)


def test_supported_models_contains_at_least_four_models():
    models = get_supported_models()
    assert len(models) >= 4
    slugs = [m["slug"] for m in models]
    assert "dell-latitude-5420" in slugs
    assert any("thinkpad" in s for s in slugs)
    assert any("elitebook" in s for s in slugs)


def test_supported_product_candidates_schema():
    candidates = get_supported_product_candidates()
    assert len(candidates) >= 4
    for c in candidates:
        assert c.manufacturer
        assert c.model
        assert c.model_year >= 2018
        assert c.specs.category.value == "LAPTOP"


def test_get_model_spec_success_cases():
    # By slug
    dell = get_model_spec("dell-latitude-5420")
    assert dell["manufacturer"] == "Dell"
    assert dell["model"] == "Latitude 5420"
    assert dell["specs"]["ram_modular"] is True
    assert dell["specs"]["ssd_modular"] is True

    # By full name
    lenovo = get_model_spec("Lenovo ThinkPad T14 Gen 1")
    assert lenovo["manufacturer"] == "Lenovo"

    # By partial/alias
    hp = get_model_spec("hp-elitebook-840-g7")
    assert hp["manufacturer"] == "HP"

    mac = get_model_spec("macbook-air-m1")
    assert mac["manufacturer"] == "Apple"


def test_get_model_spec_unsupported_model_raises_app_error():
    with pytest.raises(AppError) as exc_info:
        get_model_spec("unknown-brand-ultra-super-laptop-9000")

    err = exc_info.value
    assert err.code == UNSUPPORTED_MODEL
    assert err.http_status == 400
    assert err.field == "model"
    assert "not supported" in err.message


def test_get_model_spec_empty_query_raises_app_error():
    with pytest.raises(AppError) as exc_info:
        get_model_spec("")
    assert exc_info.value.code == UNSUPPORTED_MODEL


def test_get_repair_cost_returns_inr_with_assumptions():
    cost = get_repair_cost("dell-latitude-5420", "battery")
    assert "min" in cost
    assert "max" in cost
    assert cost["min"] > 0
    assert cost["max"] >= cost["min"]
    assert cost["basis"] == "assumption"
    assert len(cost["note"]) > 5

    ssd_cost = get_repair_cost("lenovo-thinkpad-t14-gen-1", "ssd")
    assert ssd_cost["basis"] == "assumption"


def test_get_repair_cost_unsupported_model_raises_error():
    with pytest.raises(AppError) as exc_info:
        get_repair_cost("nonexistent-laptop-xyz", "battery")
    assert exc_info.value.code == UNSUPPORTED_MODEL


def test_get_useful_life_returns_assumptions():
    life = get_useful_life("dell-latitude-5420")
    assert "baseline_years" in life
    assert "extended_years_post_repair" in life
    assert life["baseline_years"] >= 4.0
    assert life["basis"] == "assumption"
    assert len(life["note"]) > 5


def test_all_product_json_files_have_explicit_assumptions():
    products = load_all_products(force_reload=True)
    assert len(products) >= 4

    for slug, prod in products.items():
        # Repairability score must have basis: assumption
        repairability = prod.get("repairability_score", {})
        assert repairability.get("basis") == "assumption", f"{slug} missing repairability assumption basis"
        assert "note" in repairability, f"{slug} missing repairability note"

        # Typical repair costs in INR must have basis: assumption
        costs = prod.get("typical_repair_cost_inr", {})
        assert len(costs) > 0, f"{slug} has no repair costs"
        for comp, cdata in costs.items():
            assert cdata.get("basis") == "assumption", f"{slug} {comp} cost missing assumption basis"
            assert "note" in cdata, f"{slug} {comp} cost missing note"

        # Expected useful life
        useful_life = prod.get("expected_useful_life", {})
        assert useful_life.get("basis") == "assumption", f"{slug} useful life missing assumption basis"
        assert "note" in useful_life, f"{slug} useful life missing note"

        # Resale / recovery values
        recovery = prod.get("resale_recovery_values_inr", {})
        assert "whole_working" in recovery
        assert recovery["whole_working"].get("basis") == "assumption"
        for comp, rdata in recovery.get("components", {}).items():
            assert rdata.get("basis") == "assumption", f"{slug} {comp} recovery missing assumption basis"
            assert "note" in rdata, f"{slug} {comp} recovery missing note"

        # Disclaimer
        assert "disclaimer" in prod
        assert "demo" in prod["disclaimer"].lower() or "assumption" in prod["disclaimer"].lower()


def test_all_demo_cases_have_required_sections_and_assumptions():
    demo_dir = get_demo_data_dir()
    files = list(demo_dir.glob("*.json"))
    assert len(files) >= 4

    for f in files:
        import json
        with open(f, "r", encoding="utf-8") as jf:
            demo_case = json.load(jf)

        assert "id" in demo_case
        assert "title" in demo_case
        assert "product" in demo_case
        assert "vision_findings" in demo_case
        assert "diagnostics" in demo_case
        assert "user_symptoms" in demo_case

        # Check vision findings
        vis = demo_case["vision_findings"]
        assert len(vis.get("visible_damages", [])) > 0 or len(vis.get("image_names", [])) > 0
        assert vis.get("basis") == "assumption"

        # Check diagnostics have key components
        diag = demo_case["diagnostics"]
        assert "battery" in diag
        assert "ssd" in diag
        assert "ram" in diag
        assert "thermals" in diag
        assert "system" in diag
        assert diag.get("basis") == "assumption"

        # Check symptoms
        symptoms = demo_case["user_symptoms"]
        assert len(symptoms.get("reported_issues", [])) > 0
        assert symptoms.get("basis") == "assumption"
