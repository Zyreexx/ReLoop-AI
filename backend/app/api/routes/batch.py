"""
Enterprise Batch Inventory Assessment API routes.
Enables bulk device intake via CSV/JSON, background bounded processing,
fleet analytics, and CSV/Excel exports.
"""
import json
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import StreamingResponse
import io

from app.schemas.batch import BatchJobSummary
from app.schemas.enums import Objective
from app.services.batch_service import batch_service

router = APIRouter(prefix="/batch", tags=["Enterprise Batch Assessment"])


@router.post("/upload")
async def upload_batch_inventory(
    file: UploadFile = File(...),
    org_id: str = Form("default_org"),
    objective: str = Form("LOWEST_COST"),
):
    """
    Upload an enterprise hardware inventory manifest (CSV or JSON format)
    to perform automated, parallel lifecycle assessment across hundreds of devices.
    """
    filename = file.filename or "inventory.csv"
    content_bytes = await file.read()

    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content_str = content_bytes.decode("latin-1", errors="replace")

    items = []
    errors = []

    if filename.lower().endswith(".json"):
        try:
            raw_data = json.loads(content_str)
            if isinstance(raw_data, list):
                from app.schemas.batch import BatchUploadItem
                for r in raw_data:
                    items.append(BatchUploadItem(**r))
            else:
                raise ValueError("JSON must contain an array of device objects.")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON file format: {str(e)}")
    else:
        items, errors = batch_service.parse_csv_content(content_str)

    if not items:
        raise HTTPException(
            status_code=400,
            detail=f"No valid device records could be parsed. Errors: {'; '.join(errors) if errors else 'Empty file'}"
        )

    # Parse objective
    obj = Objective.LOWEST_COST
    try:
        obj = Objective(objective.upper())
    except ValueError:
        pass

    job_id = await batch_service.start_batch_job(items, org_id=org_id, user_objective=obj)

    return {
        "job_id": job_id,
        "org_id": org_id,
        "total_devices": len(items),
        "status": "PROCESSING",
        "warnings": errors,
        "poll_url": f"/api/batch/{job_id}/status",
        "summary_url": f"/api/batch/{job_id}/summary",
    }


@router.get("/{job_id}/status")
def get_batch_job_status(job_id: str):
    """Poll job progress, completion percentage, and active state."""
    summary = batch_service.get_job_summary(job_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Batch job {job_id} not found")

    pct = round((summary.processed_devices / summary.total_devices * 100), 1) if summary.total_devices > 0 else 0
    return {
        "job_id": summary.job_id,
        "status": summary.status,
        "total_devices": summary.total_devices,
        "processed_devices": summary.processed_devices,
        "successful_devices": summary.successful_devices,
        "failed_devices": summary.failed_devices,
        "completion_percentage": pct,
        "completed_at": summary.completed_at,
    }


@router.get("/{job_id}/summary", response_model=BatchJobSummary)
def get_batch_job_summary(job_id: str):
    """Retrieve complete fleet assessment summary, pathway distributions, and device records."""
    summary = batch_service.get_job_summary(job_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Batch job {job_id} not found")
    return summary


@router.post("/{job_id}/cancel")
def cancel_batch_job(job_id: str):
    """Cancel an active batch job."""
    success = batch_service.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled (already completed, failed, or non-existent)")
    return {"status": "CANCELLED", "job_id": job_id}


@router.post("/{job_id}/retry")
async def retry_failed_items(job_id: str):
    """Retry failed device items from a completed batch job."""
    success = await batch_service.retry_failed(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="No failed items found or job not eligible for retry.")
    return {"status": "RETRY_STARTED", "job_id": job_id}


@router.get("/{job_id}/export/csv")
def export_batch_csv(job_id: str):
    """Download fleet assessment results as a CSV spreadsheet."""
    try:
        csv_data = batch_service.export_csv(job_id)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=fleet_assessment_{job_id}.csv"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{job_id}/export/excel")
def export_batch_excel(job_id: str):
    """Download comprehensive fleet assessment results as a formatted Excel workbook (.xlsx)."""
    try:
        excel_bytes = batch_service.export_excel(job_id)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=fleet_assessment_{job_id}.xlsx"},
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
