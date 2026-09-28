#!/usr/bin/env python3
"""
Vision Identification Accuracy Benchmark Harness for ReLoop AI.

Evaluates model identification accuracy against labeled photo sets:
  data/vision_eval/<catalog-model-slug>/<set-name>/*.jpg

Reports:
  - Exact-model accuracy (%)
  - Manufacturer accuracy (%)
  - UNKNOWN rate (%)
  - Wrong-but-HIGH rate (%)  <-- Critical safety metric
  - Average latency (ms)

Supports multi-configuration comparison via CLI flags:
  --model, --resolution, --prompt-version (v1 or v2)

Usage:
    python scripts/eval_vision.py
    python scripts/eval_vision.py --model gemini-2.5-flash --resolution HIGH --prompt-version v2
    python scripts/eval_vision.py --data-dir data/vision_eval --output-dir data/vision_eval/results
"""
import argparse
import datetime
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import patch

# Setup sys.path to locate backend packages
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import settings
from app.knowledge.loader import get_model_spec
from app.services.vision import vision_service


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def discover_eval_sets(eval_root: Path) -> List[Dict[str, Any]]:
    """
    Discovers labeled photo sets organized under:
      data/vision_eval/<catalog-model-slug>/<set-name>/*.jpg
    """
    eval_sets = []
    if not eval_root.exists() or not eval_root.is_dir():
        return eval_sets

    for model_dir in sorted(eval_root.iterdir()):
        if not model_dir.is_dir() or model_dir.name in ["results", "__pycache__", ".git"]:
            continue

        model_slug = model_dir.name

        # Look for subdirectories (photo sets)
        subdirs = [d for d in sorted(model_dir.iterdir()) if d.is_dir() and d.name != "__pycache__"]
        if subdirs:
            for set_dir in subdirs:
                img_files = sorted(
                    [p for p in set_dir.iterdir() if p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS],
                    key=lambda p: p.name,
                )
                if img_files:
                    eval_sets.append({
                        "model_slug": model_slug,
                        "set_name": set_dir.name,
                        "set_path": set_dir,
                        "image_files": img_files,
                    })
        else:
            # Check if photos are directly in model_dir
            img_files = sorted(
                [p for p in model_dir.iterdir() if p.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS],
                key=lambda p: p.name,
            )
            if img_files:
                eval_sets.append({
                    "model_slug": model_slug,
                    "set_name": "default",
                    "set_path": model_dir,
                    "image_files": img_files,
                })

    return eval_sets


def calculate_vision_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Pure metric calculation function for vision accuracy evaluation.
    Computes:
      - exact_model_accuracy (%): predicted manufacturer + model matches expected
      - manufacturer_accuracy (%): predicted manufacturer matches expected
      - unknown_rate (%): predicted model is UNKNOWN or None
      - wrong_but_high_rate (%): prediction is WRONG but confidence evaluated as HIGH
      - avg_latency_ms: average call latency
    """
    total = len(records)
    if total == 0:
        return {
            "total_samples": 0,
            "exact_model_matches": 0,
            "exact_model_accuracy": 0.0,
            "manufacturer_matches": 0,
            "manufacturer_accuracy": 0.0,
            "unknown_count": 0,
            "unknown_rate": 0.0,
            "wrong_but_high_count": 0,
            "wrong_but_high_rate": 0.0,
            "avg_latency_ms": 0.0,
        }

    exact_model_matches = 0
    manufacturer_matches = 0
    unknown_count = 0
    wrong_but_high_count = 0
    total_latency_ms = 0.0

    for r in records:
        exp_mfr = str(r.get("expected_manufacturer") or "").strip().lower()
        exp_model = str(r.get("expected_model") or "").strip().lower()

        pred_mfr = str(r.get("predicted_manufacturer") or "").strip().lower()
        pred_model = str(r.get("predicted_model") or "").strip().lower()

        conf_level = str(r.get("confidence_level") or "").strip().upper()
        cand_id = str(r.get("candidate_id") or "").strip().upper()

        is_unknown = (
            cand_id in ["UNKNOWN", ""]
            or not pred_model
            or conf_level == "UNKNOWN"
            or r.get("is_unknown", False)
        )

        # Exact match: manufacturer matches AND model name matches
        is_exact = False
        if not is_unknown and exp_mfr == pred_mfr:
            if exp_model == pred_model:
                is_exact = True
            elif exp_model in pred_model or pred_model in exp_model:
                is_exact = True

        # Manufacturer match
        is_mfr_match = (not is_unknown) and (exp_mfr == pred_mfr)

        if is_exact:
            exact_model_matches += 1

        if is_mfr_match:
            manufacturer_matches += 1

        if is_unknown:
            unknown_count += 1

        # Wrong-but-HIGH: most dangerous failure mode
        # Model is incorrect (or unknown), but internal confidence evaluated as HIGH
        if not is_exact and conf_level == "HIGH":
            wrong_but_high_count += 1

        total_latency_ms += float(r.get("latency_ms", 0.0))

    return {
        "total_samples": total,
        "exact_model_matches": exact_model_matches,
        "exact_model_accuracy": round((exact_model_matches / total) * 100.0, 2),
        "manufacturer_matches": manufacturer_matches,
        "manufacturer_accuracy": round((manufacturer_matches / total) * 100.0, 2),
        "unknown_count": unknown_count,
        "unknown_rate": round((unknown_count / total) * 100.0, 2),
        "wrong_but_high_count": wrong_but_high_count,
        "wrong_but_high_rate": round((wrong_but_high_count / total) * 100.0, 2),
        "avg_latency_ms": round(total_latency_ms / total, 2),
    }


def run_evaluation(
    eval_sets: List[Dict[str, Any]],
    model: Optional[str] = None,
    resolution: Optional[str] = None,
    prompt_version: str = "v2",
    api_key: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Executes real identification calls for all evaluation sets and calculates summary metrics.
    Refuses to run if DEMO_FALLBACK is active.
    """
    if settings.DEMO_FALLBACK:
        raise RuntimeError(
            "ERROR: Vision evaluation cannot run with DEMO_FALLBACK=true. "
            "The evaluation harness requires real live AI inference to benchmark accuracy. "
            "Please unset DEMO_FALLBACK or set DEMO_FALLBACK=false before running."
        )

    # Apply configuration overrides
    if model:
        settings.GEMINI_MODEL = model
    if resolution:
        settings.GEMINI_MEDIA_RESOLUTION = resolution

    records = []

    for item in eval_sets:
        model_slug = item["model_slug"]
        set_name = item["set_name"]
        image_files = item["image_files"]

        # Resolve expected ground truth from catalog specs
        try:
            expected_spec = get_model_spec(model_slug)
            expected_mfr = expected_spec.get("manufacturer", "Unknown")
            expected_model = expected_spec.get("model", "Unknown")
        except Exception:
            expected_mfr = "Unknown"
            expected_model = model_slug

        # Read image bytes
        image_bytes_list = []
        for img_path in image_files:
            with open(img_path, "rb") as f:
                image_bytes_list.append(f.read())

        # Measure inference latency
        t0 = time.perf_counter()
        try:
            if prompt_version == "v1":
                from app.ai.prompt_loader import load_prompt
                with patch("app.services.vision.load_prompt", lambda name, ver: load_prompt("vision_identify", "v1")):
                    res = vision_service.identify(
                        image_bytes_list=image_bytes_list,
                        api_key=api_key,
                    )
            else:
                res = vision_service.identify(
                    image_bytes_list=image_bytes_list,
                    api_key=api_key,
                )
            latency_ms = (time.perf_counter() - t0) * 1000.0
            error_msg = None
        except Exception as e:
            latency_ms = (time.perf_counter() - t0) * 1000.0
            res = None
            error_msg = str(e)

        if res and res.identified_model:
            pred_mfr = res.identified_model.manufacturer
            pred_model = res.identified_model.model
            cand_id = res.candidate_id or "UNKNOWN"
            conf_level = getattr(res.confidence_level, "value", res.confidence_level) or "HIGH"
            conf_score = res.confidence
            source = res.source
            label_evidence = res.label_evidence
            visual_evidence = res.visual_evidence
            contradictions = res.contradictions
            is_unknown = False
        else:
            pred_mfr = None
            pred_model = None
            cand_id = res.candidate_id if res else "UNKNOWN"
            conf_level = getattr(res.confidence_level, "value", res.confidence_level) if res else "UNKNOWN"
            conf_score = res.confidence if res else 0.0
            source = res.source if res else "live"
            label_evidence = res.label_evidence if res else []
            visual_evidence = res.visual_evidence if res else []
            contradictions = res.contradictions if res else []
            is_unknown = True

        # Check match
        is_exact = (
            not is_unknown
            and pred_mfr
            and expected_mfr.lower() == pred_mfr.lower()
            and (
                expected_model.lower() == str(pred_model).lower()
                or expected_model.lower() in str(pred_model).lower()
                or str(pred_model).lower() in expected_model.lower()
            )
        )

        record = {
            "model_slug": model_slug,
            "set_name": set_name,
            "image_count": len(image_files),
            "expected_manufacturer": expected_mfr,
            "expected_model": expected_model,
            "predicted_manufacturer": pred_mfr,
            "predicted_model": pred_model,
            "candidate_id": cand_id,
            "confidence_level": conf_level,
            "confidence_score": conf_score,
            "source": source,
            "latency_ms": round(latency_ms, 2),
            "is_exact_match": is_exact,
            "is_unknown": is_unknown,
            "label_evidence": label_evidence,
            "visual_evidence": visual_evidence,
            "contradictions": contradictions,
            "error": error_msg,
        }
        records.append(record)

    metrics = calculate_vision_metrics(records)
    return records, metrics


def print_evaluation_report(
    records: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    config: Dict[str, Any],
):
    """
    Renders human-readable summary table and metrics to console.
    """
    print("\n" + "=" * 90)
    print("                      RELOOP AI - VISION ACCURACY BENCHMARK")
    print("=" * 90)
    print(f"Configuration: Model: {config.get('model')} | Resolution: {config.get('resolution')} | Prompt: {config.get('prompt_version')}")
    print("-" * 90)

    # Per-sample table
    header = f"{'#':<3} | {'Model Slug':<24} | {'Set':<10} | {'Expected Model':<20} | {'Predicted Model':<20} | {'Conf':<6} | {'Latency':<8} | {'Match'}"
    print(header)
    print("-" * 90)

    for i, r in enumerate(records, 1):
        slug = r['model_slug'][:24]
        s_name = r['set_name'][:10]
        exp = f"{r['expected_manufacturer']} {r['expected_model']}"[:20]
        pred = f"{r['predicted_manufacturer'] or ''} {r['predicted_model'] or 'UNKNOWN'}"[:20]
        conf = str(r['confidence_level'])[:6]
        lat = f"{r['latency_ms']:.0f}ms"
        match_str = "PASS" if r['is_exact_match'] else ("UNKNOWN" if r['is_unknown'] else "FAIL")

        print(f"{i:<3} | {slug:<24} | {s_name:<10} | {exp:<20} | {pred:<20} | {conf:<6} | {lat:<8} | {match_str}")

    print("-" * 90)
    print("SUMMARY METRICS:")
    print(f"  Total Evaluated Sets:    {metrics['total_samples']}")
    print(f"  Exact-Model Accuracy:    {metrics['exact_model_accuracy']}% ({metrics['exact_model_matches']}/{metrics['total_samples']})")
    print(f"  Manufacturer Accuracy:   {metrics['manufacturer_accuracy']}% ({metrics['manufacturer_matches']}/{metrics['total_samples']})")
    print(f"  UNKNOWN Rate:            {metrics['unknown_rate']}% ({metrics['unknown_count']}/{metrics['total_samples']})")
    print(f"  Wrong-but-HIGH Rate:     {metrics['wrong_but_high_rate']}% ({metrics['wrong_but_high_count']}/{metrics['total_samples']})  <-- Safety Risk")
    print(f"  Average Latency:         {metrics['avg_latency_ms']} ms")
    print("=" * 90 + "\n")


def save_results(
    output_dir: Path,
    records: List[Dict[str, Any]],
    metrics: Dict[str, Any],
    config: Dict[str, Any],
) -> Path:
    """
    Saves evaluation run results to timestamped JSON artifact.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_file = output_dir / f"eval_vision_{ts}.json"

    data = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "config": config,
        "summary": metrics,
        "results": records,
    }

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    return out_file


def main():
    parser = argparse.ArgumentParser(description="ReLoop AI Vision Identification Accuracy Benchmark Harness")
    parser.add_argument("--model", type=str, default=settings.GEMINI_MODEL, help="Gemini model name override (e.g. gemini-2.5-flash)")
    parser.add_argument("--resolution", type=str, default=settings.GEMINI_MEDIA_RESOLUTION, help="Media resolution override (e.g. HIGH, MEDIUM, LOW)")
    parser.add_argument("--prompt-version", type=str, default="v2", choices=["v1", "v2"], help="Prompt version to benchmark (v1 or v2)")
    parser.add_argument("--data-dir", type=str, default="data/vision_eval", help="Path to vision eval images directory")
    parser.add_argument("--output-dir", type=str, default="data/vision_eval/results", help="Path to save output benchmark JSON files")
    parser.add_argument("--api-key", type=str, default=None, help="Optional custom Gemini API key")

    args = parser.parse_args()

    eval_root = REPO_ROOT / args.data_dir if not Path(args.data_dir).is_absolute() else Path(args.data_dir)
    results_dir = REPO_ROOT / args.output_dir if not Path(args.output_dir).is_absolute() else Path(args.output_dir)

    print(f"Discovering evaluation sets under: {eval_root}")
    eval_sets = discover_eval_sets(eval_root)

    if not eval_sets:
        print(f"No evaluation sets found under {eval_root}.")
        print("Please place image folders under data/vision_eval/<catalog-model-slug>/<set-name>/*.jpg")
        print("See data/vision_eval/README.md for details.")
        return

    config = {
        "model": args.model,
        "resolution": args.resolution,
        "prompt_version": args.prompt_version,
        "data_dir": str(eval_root),
    }

    try:
        records, metrics = run_evaluation(
            eval_sets=eval_sets,
            model=args.model,
            resolution=args.resolution,
            prompt_version=args.prompt_version,
            api_key=args.api_key,
        )
    except Exception as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(1)

    print_evaluation_report(records, metrics, config)
    out_path = save_results(results_dir, records, metrics, config)
    print(f"Saved benchmark results to: {out_path}")


if __name__ == "__main__":
    main()
