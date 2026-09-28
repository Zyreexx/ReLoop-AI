"""
Unit tests for vision accuracy benchmark metrics calculation in scripts/eval_vision.py.
Uses fake predictions with no real API calls.
"""
from pathlib import Path
import pytest

import sys
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.eval_vision import (
    calculate_vision_metrics,
    discover_eval_sets,
    run_evaluation,
)
from app.config import settings


def test_calculate_vision_metrics_empty():
    metrics = calculate_vision_metrics([])
    assert metrics["total_samples"] == 0
    assert metrics["exact_model_accuracy"] == 0.0
    assert metrics["manufacturer_accuracy"] == 0.0
    assert metrics["unknown_rate"] == 0.0
    assert metrics["wrong_but_high_rate"] == 0.0
    assert metrics["avg_latency_ms"] == 0.0


def test_calculate_vision_metrics_all_exact_matches():
    records = [
        {
            "expected_manufacturer": "Dell",
            "expected_model": "Latitude 5420",
            "predicted_manufacturer": "Dell",
            "predicted_model": "Latitude 5420",
            "candidate_id": "C2",
            "confidence_level": "HIGH",
            "latency_ms": 1000.0,
        },
        {
            "expected_manufacturer": "Lenovo",
            "expected_model": "ThinkPad T14 Gen 1",
            "predicted_manufacturer": "Lenovo",
            "predicted_model": "ThinkPad T14 Gen 1",
            "candidate_id": "C4",
            "confidence_level": "HIGH",
            "latency_ms": 2000.0,
        },
    ]

    metrics = calculate_vision_metrics(records)
    assert metrics["total_samples"] == 2
    assert metrics["exact_model_matches"] == 2
    assert metrics["exact_model_accuracy"] == 100.0
    assert metrics["manufacturer_matches"] == 2
    assert metrics["manufacturer_accuracy"] == 100.0
    assert metrics["unknown_count"] == 0
    assert metrics["unknown_rate"] == 0.0
    assert metrics["wrong_but_high_count"] == 0
    assert metrics["wrong_but_high_rate"] == 0.0
    assert metrics["avg_latency_ms"] == 1500.0


def test_calculate_vision_metrics_all_unknown():
    records = [
        {
            "expected_manufacturer": "Dell",
            "expected_model": "Latitude 5420",
            "predicted_manufacturer": None,
            "predicted_model": None,
            "candidate_id": "UNKNOWN",
            "confidence_level": "UNKNOWN",
            "latency_ms": 800.0,
        },
        {
            "expected_manufacturer": "Apple",
            "expected_model": "MacBook Air (M1, 2020)",
            "predicted_manufacturer": None,
            "predicted_model": None,
            "candidate_id": "UNKNOWN",
            "confidence_level": "UNKNOWN",
            "latency_ms": 1200.0,
        },
    ]

    metrics = calculate_vision_metrics(records)
    assert metrics["total_samples"] == 2
    assert metrics["exact_model_matches"] == 0
    assert metrics["exact_model_accuracy"] == 0.0
    assert metrics["manufacturer_matches"] == 0
    assert metrics["manufacturer_accuracy"] == 0.0
    assert metrics["unknown_count"] == 2
    assert metrics["unknown_rate"] == 100.0
    assert metrics["wrong_but_high_count"] == 0
    assert metrics["wrong_but_high_rate"] == 0.0
    assert metrics["avg_latency_ms"] == 1000.0


def test_calculate_vision_metrics_brand_match_only():
    records = [
        {
            "expected_manufacturer": "HP",
            "expected_model": "EliteBook 840 G7",
            "predicted_manufacturer": "HP",
            "predicted_model": "ProBook 450",
            "candidate_id": "C3",
            "confidence_level": "MEDIUM",
            "latency_ms": 1100.0,
        }
    ]

    metrics = calculate_vision_metrics(records)
    assert metrics["total_samples"] == 1
    assert metrics["exact_model_matches"] == 0
    assert metrics["exact_model_accuracy"] == 0.0
    assert metrics["manufacturer_matches"] == 1
    assert metrics["manufacturer_accuracy"] == 100.0
    assert metrics["unknown_count"] == 0
    assert metrics["unknown_rate"] == 0.0
    assert metrics["wrong_but_high_count"] == 0
    assert metrics["wrong_but_high_rate"] == 0.0


def test_calculate_vision_metrics_wrong_but_high_detection():
    """
    Most damaging failure mode: model predicted is wrong, but confidence evaluated as HIGH.
    """
    records = [
        # Correct sample
        {
            "expected_manufacturer": "Dell",
            "expected_model": "Latitude 5420",
            "predicted_manufacturer": "Dell",
            "predicted_model": "Latitude 5420",
            "candidate_id": "C2",
            "confidence_level": "HIGH",
            "latency_ms": 1000.0,
        },
        # Wrong model with HIGH confidence (dangerous!)
        {
            "expected_manufacturer": "HP",
            "expected_model": "EliteBook 840 G7",
            "predicted_manufacturer": "Lenovo",
            "predicted_model": "ThinkPad T14 Gen 1",
            "candidate_id": "C4",
            "confidence_level": "HIGH",
            "latency_ms": 1200.0,
        },
        # Unknown with UNKNOWN confidence (safe failure)
        {
            "expected_manufacturer": "Apple",
            "expected_model": "MacBook Air (M1, 2020)",
            "predicted_manufacturer": None,
            "predicted_model": None,
            "candidate_id": "UNKNOWN",
            "confidence_level": "UNKNOWN",
            "latency_ms": 900.0,
        },
        # Wrong model with LOW confidence (safe failure)
        {
            "expected_manufacturer": "Dell",
            "expected_model": "Latitude 5420",
            "predicted_manufacturer": "HP",
            "predicted_model": "EliteBook 840 G7",
            "candidate_id": "C3",
            "confidence_level": "LOW",
            "latency_ms": 1100.0,
        },
    ]

    metrics = calculate_vision_metrics(records)
    assert metrics["total_samples"] == 4
    assert metrics["exact_model_matches"] == 1
    assert metrics["exact_model_accuracy"] == 25.0
    assert metrics["manufacturer_matches"] == 1
    assert metrics["manufacturer_accuracy"] == 25.0
    assert metrics["unknown_count"] == 1
    assert metrics["unknown_rate"] == 25.0
    assert metrics["wrong_but_high_count"] == 1
    assert metrics["wrong_but_high_rate"] == 25.0
    assert metrics["avg_latency_ms"] == 1050.0


def test_discover_eval_sets(tmp_path: Path):
    # Setup mock folder structure
    model_dir = tmp_path / "dell-latitude-5420"
    set1_dir = model_dir / "set-01"
    set1_dir.mkdir(parents=True)
    (set1_dir / "01_front.jpg").write_bytes(b"test1")
    (set1_dir / "02_back.png").write_bytes(b"test2")
    (set1_dir / "notes.txt").write_text("not an image")

    set2_dir = model_dir / "set-02"
    set2_dir.mkdir(parents=True)
    (set2_dir / "01_lid.webp").write_bytes(b"test3")

    eval_sets = discover_eval_sets(tmp_path)
    assert len(eval_sets) == 2
    assert eval_sets[0]["model_slug"] == "dell-latitude-5420"
    assert eval_sets[0]["set_name"] == "set-01"
    assert len(eval_sets[0]["image_files"]) == 2
    assert eval_sets[1]["set_name"] == "set-02"
    assert len(eval_sets[1]["image_files"]) == 1


def test_run_evaluation_refuses_when_demo_fallback_active(monkeypatch):
    monkeypatch.setattr(settings, "DEMO_FALLBACK", True)
    with pytest.raises(RuntimeError, match="DEMO_FALLBACK=true"):
        run_evaluation(eval_sets=[{"model_slug": "dell-latitude-5420", "set_name": "set-01", "image_files": []}])
