"""
Schemas for Enterprise Batch Inventory Assessment.
Supports multi-device intake via CSV and JSON, bounded concurrency tracking,
and aggregated fleet-level analytics.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class BatchUploadItem(BaseModel):
    asset_id: str
    make: str = "Generic"
    model: str
    serial_number: Optional[str] = None
    cpu: Optional[str] = None
    ram_gb: Optional[int] = None
    storage_gb: Optional[int] = None
    reported_issues: Optional[str] = None
    battery_cycles: Optional[int] = None
    battery_capacity_percent: Optional[float] = None
    cosmetic_condition: Optional[str] = None  # "GOOD", "FAIR", "SCRATCHED", "CRACKED"
    org_id: Optional[str] = None


class BatchDeviceResult(BaseModel):
    asset_id: str
    product_id: str
    model: str
    status: str = "SUCCESS"  # "SUCCESS" | "FAILED"
    error_message: Optional[str] = None
    primary_pathway: Optional[str] = None
    primary_score: Optional[float] = None
    estimated_cost_inr: Optional[float] = None
    estimated_carbon_avoided_kg: Optional[float] = None
    extended_life_months: Optional[float] = None
    condition_summary: Optional[str] = None
    processed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BatchJobSummary(BaseModel):
    job_id: str
    org_id: str = "default_org"
    status: str = "QUEUED"  # "QUEUED", "PROCESSING", "COMPLETED", "FAILED", "CANCELLED"
    total_devices: int = 0
    processed_devices: int = 0
    successful_devices: int = 0
    failed_devices: int = 0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    pathway_counts: Dict[str, int] = Field(default_factory=dict)
    total_cost_inr: float = 0.0
    total_carbon_avoided_kg: float = 0.0
    devices: List[BatchDeviceResult] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

