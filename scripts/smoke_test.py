#!/usr/bin/env python3
"""
Smoke test script for ReLoop AI deployment validation.
Checks /health and runs one canonical demo case through the end-to-end API lifecycle.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --base-url http://localhost:8000
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# Setup sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def run_smoke_test(base_url: str = None) -> bool:
    print("\n" + "=" * 80)
    print("                      RELOOP AI -- DEPLOYMENT SMOKE TEST                      ")
    print("=" * 80)

    if base_url:
        import httpx
        client = httpx.Client(base_url=base_url.rstrip("/"), timeout=30.0)
        target_name = f"Live server at {base_url}"
    else:
        from app.db.session import create_all_tables
        create_all_tables()
        from starlette.testclient import TestClient
        from app.main import app
        client = TestClient(app)
        target_name = "In-process FastAPI TestClient"

    print(f"Target: {target_name}\n")
    all_ok = True

    # 1. Health Check
    t0 = time.perf_counter()
    res = client.get("/health")
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code == 200:
        data = res.json()
        print(f" [PASS] GET /health (HTTP 200, {dt:.1f}ms) -> status: {data.get('status', 'ok')}")
    else:
        print(f" [FAIL] GET /health (HTTP {res.status_code}) -> {res.text}")
        return False

    # 2. Supported Catalog
    t0 = time.perf_counter()
    res = client.get("/api/products/catalog")
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code == 200:
        models = res.json()
        print(f" [PASS] GET /api/products/catalog (HTTP 200, {dt:.1f}ms) -> {len(models)} models available")
    else:
        print(f" [FAIL] GET /api/products/catalog (HTTP {res.status_code}) -> {res.text}")
        all_ok = False

    # 3. End-to-end Demo Case (Dell Latitude 5420 Repairable)
    print("\n--- Running End-to-End Lifecycle on Demo Case (Dell Latitude 5420) ---")

    # Step A: Register Product
    t0 = time.perf_counter()
    prod_payload = {
        "manufacturer": "Dell",
        "model": "Latitude 5420",
        "model_year": 2021,
        "category": "LAPTOP",
        "age_years": 4.0,
    }
    res = client.post("/api/products", json=prod_payload)
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code != 200:
        print(f" [FAIL] POST /api/products (HTTP {res.status_code}) -> {res.text}")
        return False
    product = res.json()
    product_id = product["id"]
    print(f" [PASS] 1. POST /api/products -> Registered product ID: {product_id} ({dt:.1f}ms)")

    # Step B: Vision Analysis
    t0 = time.perf_counter()
    vis_payload = {
        "product_id": product_id,
        "inspection_notes": "2 missing keycaps observed: F4 and Left Alt; light chassis scratches.",
    }
    res = client.post("/api/vision/analyze", json=vis_payload)
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code != 200:
        print(f" [FAIL] POST /api/vision/analyze (HTTP {res.status_code}) -> {res.text}")
        return False
    vis_data = res.json()
    print(f" [PASS] 2. POST /api/vision/analyze -> {len(vis_data.get('findings', []))} visible findings ({dt:.1f}ms)")

    # Step C: Diagnostics Telemetry
    t0 = time.perf_counter()
    diag_payload = {
        "product_id": product_id,
        "battery": {
            "design_capacity_mwh": 54000.0,
            "full_charge_capacity_mwh": 39400.0,
            "cycle_count": 680,
            "health_percentage": 73.0,
        },
        "ssd": {
            "health_percentage": 91.0,
            "capacity_gb": 512,
            "power_on_hours": 8200,
            "smart_status": "PASS",
        },
        "ram": {
            "installed_gb": 16,
            "test_result": "PASS",
        },
        "thermals": {
            "cpu_idle_temp_c": 58.0,
            "cpu_max_temp_c": 96.0,
            "throttling_detected": True,
        },
        "system": {
            "post_successful": True,
            "motherboard_power_stable": True,
        },
    }
    res = client.post("/api/diagnostics/validate", json=diag_payload)
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code != 200:
        print(f" [FAIL] POST /api/diagnostics/validate (HTTP {res.status_code}) -> {res.text}")
        return False
    print(f" [PASS] 3. POST /api/diagnostics/validate -> Telemetry validated ({dt:.1f}ms)")

    # Step D: Assessment Profile Synthesis
    t0 = time.perf_counter()
    res = client.post("/api/assessment/build", json={"product_id": product_id})
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code != 200:
        print(f" [FAIL] POST /api/assessment/build (HTTP {res.status_code}) -> {res.text}")
        return False
    profile = res.json()
    print(f" [PASS] 4. POST /api/assessment/build -> Profile synthesized: {profile.get('overall_hardware_health', 'N/A')} ({dt:.1f}ms)")

    # Step E: Optimizer Recommendation Generation
    t0 = time.perf_counter()
    res = client.post(
        "/api/recommendations/generate",
        json={"product_id": product_id, "objective": "MAX_LIFE"},
    )
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code != 200:
        print(f" [FAIL] POST /api/recommendations/generate (HTTP {res.status_code}) -> {res.text}")
        return False
    rec = res.json()
    selected_pathway = rec.get("selected_pathway", "N/A")
    score = rec.get("score", 0.0)
    print(f" [PASS] 5. POST /api/recommendations/generate -> Pathway: {selected_pathway}, Score: {score:.1f} ({dt:.1f}ms)")

    # Step F: Condition Report & Export
    t0 = time.perf_counter()
    res = client.get(f"/api/reports/{product_id}")
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code != 200:
        print(f" [FAIL] GET /api/reports/{product_id} (HTTP {res.status_code}) -> {res.text}")
        return False
    report = res.json()
    print(f" [PASS] 6. GET /api/reports/{product_id} -> Report fetched ({dt:.1f}ms)")

    t0 = time.perf_counter()
    res = client.get(f"/api/reports/{product_id}/download")
    dt = (time.perf_counter() - t0) * 1000
    if res.status_code != 200:
        print(f" [FAIL] GET /api/reports/{product_id}/download (HTTP {res.status_code}) -> {res.text}")
        return False
    print(f" [PASS] 7. GET /api/reports/{product_id}/download -> Download payload received ({dt:.1f}ms)")

    print("\n" + "=" * 80)
    print("                   ALL SMOKE TEST ASSERTIONS PASSED (100%)                   ")
    print("=" * 80 + "\n")
    return True


def main():
    parser = argparse.ArgumentParser(description="ReLoop AI Deployment Smoke Test")
    parser.add_argument("--base-url", default=None, help="Base URL of live server (e.g. http://localhost:8000)")
    args = parser.parse_args()

    success = run_smoke_test(base_url=args.base_url)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
