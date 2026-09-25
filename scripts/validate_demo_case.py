#!/usr/bin/env python3
"""
Demo Case Validation Script for ReLoop AI.
Runs all 4 demo cases through the end-to-end API pipeline:
  Product Registration -> Vision Analysis -> Diagnostic Intake -> Assessment Synthesis -> Recommendation -> Condition Report
Asserts expected circular pathway outcomes and outputs a structured pass/fail table.

Usage:
    python scripts/validate_demo_case.py
    python scripts/validate_demo_case.py --base-url http://localhost:8000
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Setup sys.path to locate backend packages
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def load_demo_cases() -> List[dict]:
    demo_dir = REPO_ROOT / "data" / "demo"
    if not demo_dir.exists():
        demo_dir = BACKEND_DIR.parent / "data" / "demo"

    cases = []
    for f in sorted(demo_dir.glob("*.json")):
        with open(f, "r", encoding="utf-8") as jf:
            cases.append(json.load(jf))
    return cases


class ApiClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url.rstrip("/") if base_url else None
        if not self.base_url:
            from app.db.session import create_all_tables
            create_all_tables()
            from starlette.testclient import TestClient
            from app.main import app
            self.client = TestClient(app)
        else:
            import httpx
            self.client = httpx.Client(base_url=self.base_url, timeout=30.0)

    def post(self, path: str, json_data: dict) -> Tuple[int, dict]:
        if self.base_url:
            res = self.client.post(path, json=json_data)
            return res.status_code, res.json()
        else:
            res = self.client.post(path, json=json_data)
            return res.status_code, res.json()

    def get(self, path: str) -> Tuple[int, dict]:
        if self.base_url:
            res = self.client.get(path)
            return res.status_code, res.json()
        else:
            res = self.client.get(path)
            return res.status_code, res.json()


def run_demo_case(client: ApiClient, case: dict) -> Dict[str, Any]:
    case_id = case["id"]
    prod_info = case["product"]
    expected_primary = case["expected_pathway"]["primary"].upper()
    user_symptoms = case.get("user_symptoms", {})
    target_objective = user_symptoms.get("target_objective", "MAX_LIFE").upper()

    t0 = time.perf_counter()

    # Step 1: Register Product
    prod_payload = {
        "manufacturer": prod_info["manufacturer"],
        "model": prod_info["model"],
        "model_year": prod_info.get("model_year", 2021),
        "category": "LAPTOP",
        "age_years": float(prod_info.get("age_years", 3.0)),
    }
    status_code, prod_res = client.post("/api/products", prod_payload)
    if status_code != 200:
        return {
            "case_id": case_id,
            "model": f"{prod_info['manufacturer']} {prod_info['model']}",
            "objective": target_objective,
            "expected": expected_primary,
            "actual": "ERROR",
            "score": 0.0,
            "expl_source": "N/A",
            "status": "FAIL",
            "duration_ms": (time.perf_counter() - t0) * 1000,
            "error": f"Product registration failed (HTTP {status_code}): {prod_res}",
        }
    product_id = prod_res["id"]

    # Step 2: Optical / Vision Analysis
    vision_notes = f"Simulated inspection for {prod_info['manufacturer']} {prod_info['model']}"
    if "vision_findings" in case:
        damages = [d.get("description", "") for d in case["vision_findings"].get("visible_damages", [])]
        if damages:
            vision_notes = "; ".join(damages)

    status_code, vis_res = client.post(
        "/api/vision/analyze",
        {"product_id": product_id, "inspection_notes": vision_notes},
    )
    if status_code != 200:
        return {
            "case_id": case_id,
            "model": f"{prod_info['manufacturer']} {prod_info['model']}",
            "objective": target_objective,
            "expected": expected_primary,
            "actual": "ERROR",
            "score": 0.0,
            "expl_source": "N/A",
            "status": "FAIL",
            "duration_ms": (time.perf_counter() - t0) * 1000,
            "error": f"Vision analysis failed (HTTP {status_code}): {vis_res}",
        }

    # Step 3: Diagnostic Telemetry Validation
    diag_data = case.get("diagnostics", {})
    cleaned_diags = {k: v for k, v in diag_data.items() if k not in ["basis", "note"] and isinstance(v, dict)}
    status_code, diag_res = client.post(
        "/api/diagnostics/validate",
        {"product_id": product_id, "diagnostics": cleaned_diags},
    )
    if status_code != 200:
        return {
            "case_id": case_id,
            "model": f"{prod_info['manufacturer']} {prod_info['model']}",
            "objective": target_objective,
            "expected": expected_primary,
            "actual": "ERROR",
            "score": 0.0,
            "expl_source": "N/A",
            "status": "FAIL",
            "duration_ms": (time.perf_counter() - t0) * 1000,
            "error": f"Diagnostic validation failed (HTTP {status_code}): {diag_res}",
        }

    # Step 4: Assessment Profile Synthesis
    status_code, assess_res = client.post(
        "/api/assessment/build",
        {"product_id": product_id},
    )
    if status_code != 200:
        return {
            "case_id": case_id,
            "model": f"{prod_info['manufacturer']} {prod_info['model']}",
            "objective": target_objective,
            "expected": expected_primary,
            "actual": "ERROR",
            "score": 0.0,
            "expl_source": "N/A",
            "status": "FAIL",
            "duration_ms": (time.perf_counter() - t0) * 1000,
            "error": f"Assessment build failed (HTTP {status_code}): {assess_res}",
        }

    # Step 5: Circular Pathway Recommendation
    status_code, rec_res = client.post(
        "/api/recommendations/generate",
        {"product_id": product_id, "objective": target_objective},
    )
    if status_code != 200:
        return {
            "case_id": case_id,
            "model": f"{prod_info['manufacturer']} {prod_info['model']}",
            "objective": target_objective,
            "expected": expected_primary,
            "actual": "ERROR",
            "score": 0.0,
            "expl_source": "N/A",
            "status": "FAIL",
            "duration_ms": (time.perf_counter() - t0) * 1000,
            "error": f"Recommendation generation failed (HTTP {status_code}): {rec_res}",
        }

    actual_primary = rec_res.get("selected_pathway", "").upper()
    score = float(rec_res.get("score", 0.0))
    expl = rec_res.get("explanation", {})
    expl_source = expl.get("source", "template") if isinstance(expl, dict) else "template"

    # Step 6: Condition Report Verification
    status_code, report_res = client.get(f"/api/reports/{product_id}")
    if status_code != 200:
        return {
            "case_id": case_id,
            "model": f"{prod_info['manufacturer']} {prod_info['model']}",
            "objective": target_objective,
            "expected": expected_primary,
            "actual": actual_primary,
            "score": score,
            "expl_source": expl_source,
            "status": "FAIL",
            "duration_ms": (time.perf_counter() - t0) * 1000,
            "error": f"Report retrieval failed (HTTP {status_code}): {report_res}",
        }

    duration_ms = (time.perf_counter() - t0) * 1000
    is_pass = (actual_primary == expected_primary)

    return {
        "case_id": case_id,
        "model": f"{prod_info['manufacturer']} {prod_info['model']}",
        "objective": target_objective,
        "expected": expected_primary,
        "actual": actual_primary,
        "score": score,
        "expl_source": expl_source,
        "status": "PASS" if is_pass else "FAIL",
        "duration_ms": duration_ms,
        "error": None if is_pass else f"Expected {expected_primary}, got {actual_primary}",
    }


def print_results_table(results: List[Dict[str, Any]]) -> bool:
    print("\n" + "=" * 98)
    print("                      RELOOP AI -- DEMO CASE VALIDATION SUITE                      ")
    print("=" * 98)
    header = f"{'Case ID':<22} | {'Model':<24} | {'Objective':<16} | {'Expected':<12} | {'Actual':<12} | {'Score':<5} | {'Expl':<8} | {'Status':<6}"
    print(header)
    print("-" * 98)

    all_passed = True
    for r in results:
        row = f"{r['case_id']:<22} | {r['model'][:24]:<24} | {r['objective']:<16} | {r['expected']:<12} | {r['actual']:<12} | {r['score']:<5.1f} | {r['expl_source']:<8} | {r['status']:<6}"
        print(row)
        if r["status"] != "PASS":
            all_passed = False
            if r.get("error"):
                print(f"   --> Error: {r['error']}")

    print("-" * 98)
    passed_count = sum(1 for r in results if r["status"] == "PASS")
    total_count = len(results)
    print(f"Summary: {passed_count}/{total_count} Demo Cases Validated Successfully")
    print("=" * 98 + "\n")
    return all_passed


def main():
    parser = argparse.ArgumentParser(description="ReLoop AI Demo Case Validation Suite")
    parser.add_argument("--base-url", default=None, help="Base URL of live ReLoop AI backend (e.g. http://localhost:8000)")
    args = parser.parse_args()

    demo_cases = load_demo_cases()
    if not demo_cases:
        print("ERROR: No demo cases found in data/demo/.")
        sys.exit(1)

    mode_str = f"Live API at {args.base_url}" if args.base_url else "In-process FastAPI TestClient"
    print(f"Running validation for {len(demo_cases)} demo cases using {mode_str}...")

    client = ApiClient(base_url=args.base_url)
    results = []
    for case in demo_cases:
        res = run_demo_case(client, case)
        results.append(res)

    all_passed = print_results_table(results)
    if not all_passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
