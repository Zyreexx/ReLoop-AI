"""
Tests for Enterprise Batch Inventory Assessment.
Validates CSV/JSON parsing, duplicate detection, bounded async processing,
fleet analytics aggregation, and CSV/Excel export generation.
"""
import io
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.batch_service import batch_service

client = TestClient(app)

SAMPLE_CSV = """Asset ID,Make,Model,Serial Number,RAM (GB),Storage (GB),Battery Health %,Reported Issues,Cosmetic Condition
IT-001,Lenovo,ThinkPad T14 Gen 1,SN1001,16,512,88,Battery draining fast,GOOD
IT-002,Dell,Latitude 5420,SN1002,16,256,65,Overheating and fan noise,FAIR
IT-003,Apple,MacBook Air M1,SN1003,8,256,92,None,GOOD
IT-004,HP,EliteBook 840 G7,SN1004,16,512,45,Cracked screen,CRACKED
"""

DUPLICATE_CSV = """Asset ID,Make,Model,Serial Number
IT-001,Lenovo,ThinkPad T14 Gen 1,SN1001
IT-001,Lenovo,ThinkPad T14 Gen 1,SN1002
IT-002,Dell,Latitude 5420,SN1001
"""


def test_parse_csv_content_and_duplicates():
    items, errors = batch_service.parse_csv_content(DUPLICATE_CSV)
    # IT-001 duplicate should be skipped
    assert len(items) == 2
    assert any("Duplicate Asset ID 'IT-001'" in e for e in errors)
    assert any("Duplicate Serial Number 'SN1001'" in e for e in errors)


def test_batch_upload_and_processing_end_to_end():
    # 1. Upload sample batch CSV
    file_bytes = SAMPLE_CSV.encode("utf-8")
    resp = client.post(
        "/api/batch/upload",
        files={"file": ("inventory.csv", file_bytes, "text/csv")},
        data={"org_id": "test_corp", "objective": "LOWEST_COST"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    job_id = data["job_id"]
    assert data["total_devices"] == 4

    # 2. Wait for async processing to complete (bounded workers)
    for _ in range(50):
        st_resp = client.get(f"/api/batch/{job_id}/status")
        assert st_resp.status_code == 200
        st = st_resp.json()
        if st["status"] in ["COMPLETED", "FAILED"]:
            break
        time.sleep(0.5)

    assert st["status"] == "COMPLETED"
    assert st["processed_devices"] == 4
    assert st["successful_devices"] == 4

    # 3. Retrieve Fleet Summary
    sum_resp = client.get(f"/api/batch/{job_id}/summary")
    assert sum_resp.status_code == 200
    summary = sum_resp.json()
    assert summary["total_devices"] == 4
    assert summary["successful_devices"] == 4
    assert len(summary["devices"]) == 4
    assert summary["total_carbon_avoided_kg"] > 0
    assert "pathway_counts" in summary
    assert len(summary["pathway_counts"]) >= 1

    # 4. Verify CSV Export
    csv_resp = client.get(f"/api/batch/{job_id}/export/csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "Asset ID,Model,Assessment Status" in csv_resp.text
    assert "IT-001" in csv_resp.text

    # 5. Verify Excel Export
    excel_resp = client.get(f"/api/batch/{job_id}/export/excel")
    assert excel_resp.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in excel_resp.headers["content-type"]
    assert len(excel_resp.content) > 1000  # Valid XLSX archive


def test_batch_cancel_job():
    job_id = "test_cancel_job"
    from app.schemas.batch import BatchJobSummary
    batch_service.jobs[job_id] = BatchJobSummary(
        job_id=job_id,
        org_id="cancel_org",
        status="PROCESSING",
        total_devices=10,
    )
    resp = client.post(f"/api/batch/{job_id}/cancel")
    assert resp.status_code == 200
    assert resp.json()["status"] == "CANCELLED"
    assert batch_service.jobs[job_id].status == "CANCELLED"
