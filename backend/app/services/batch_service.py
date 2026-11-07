"""
Enterprise Batch Inventory Assessment Service.
Coordinates multi-device ingestion, bounded asynchronous worker processing,
duplicate detection, fleet analytics aggregation, and report generation (CSV & Excel).
"""
import asyncio
import csv
import io
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from app.db.store import store
from app.db.session import SessionLocal
from app.schemas.batch import BatchDeviceResult, BatchJobSummary, BatchUploadItem
from app.schemas.enums import DeviceCategory, EvidenceType, Objective
from app.schemas.evidence import EvidenceItem
from app.schemas.product import ProductRecord, ProductSpecs
from app.schemas.recommendation import RecommendationRequest
from app.services.assessment_service import assessment_service
from app.services.recommendation_service import recommendation_service

logger = logging.getLogger("reloop-ai.batch_service")


class BatchAssessmentService:
    def __init__(self, max_concurrency: int = 8):
        self.max_concurrency = max_concurrency
        self.jobs: Dict[str, BatchJobSummary] = {}
        self._raw_items: Dict[str, List[BatchUploadItem]] = {}
        self._cancel_flags: Set[str] = set()

    def parse_csv_content(self, content_str: str) -> Tuple[List[BatchUploadItem], List[str]]:
        """Parses CSV text into normalized BatchUploadItem objects with duplicate detection."""
        items: List[BatchUploadItem] = []
        errors: List[str] = []
        reader = csv.DictReader(io.StringIO(content_str))

        if not reader.fieldnames:
            return [], ["Empty or malformed CSV file: no headers detected."]

        # Header normalization map
        norm_headers = {h.lower().replace(" ", "").replace("_", "").replace("-", ""): h for h in reader.fieldnames}

        def get_val(row: dict, *candidates: str) -> Optional[str]:
            for c in candidates:
                norm_c = c.lower().replace(" ", "").replace("_", "").replace("-", "")
                if norm_c in norm_headers:
                    val = row.get(norm_headers[norm_c])
                    if val is not None and str(val).strip():
                        return str(val).strip()
            return None

        seen_assets: Set[str] = set()
        seen_serials: Set[str] = set()

        for idx, row in enumerate(reader, start=2):
            asset_id = get_val(row, "asset_id", "assetid", "id", "tag")
            model = get_val(row, "model", "model_name", "product_model", "device")
            make = get_val(row, "make", "brand", "manufacturer") or "Generic"
            serial = get_val(row, "serial", "serial_number", "sn")

            if not asset_id:
                asset_id = f"ASSET-{idx:04d}"
            if not model:
                errors.append(f"Row {idx}: Missing mandatory 'model' field. Skipped.")
                continue

            # Duplicate checks
            if asset_id in seen_assets:
                errors.append(f"Row {idx}: Duplicate Asset ID '{asset_id}' detected. Skipped duplicate.")
                continue
            seen_assets.add(asset_id)

            if serial:
                if serial in seen_serials:
                    errors.append(f"Row {idx}: Duplicate Serial Number '{serial}' for asset '{asset_id}'.")
                else:
                    seen_serials.add(serial)

            # Optional hardware parameters
            ram_str = get_val(row, "ram", "ram_gb", "memory")
            storage_str = get_val(row, "storage", "storage_gb", "ssd_gb", "hdd")
            cycles_str = get_val(row, "battery_cycles", "cycles", "cycle_count")
            cap_str = get_val(row, "battery_health", "battery_percent", "health_percent")
            cosmetic = get_val(row, "cosmetic", "cosmetic_condition", "physical_condition")
            issues = get_val(row, "issues", "reported_issues", "symptoms", "faults")
            org_id = get_val(row, "org_id", "organization", "company")

            ram_val = int(ram_str) if ram_str and ram_str.isdigit() else None
            storage_val = int(storage_str) if storage_str and storage_str.isdigit() else None
            cycles_val = int(cycles_str) if cycles_str and cycles_str.isdigit() else None
            cap_val = float(cap_str) if cap_str and cap_str.replace(".", "", 1).isdigit() else None

            items.append(
                BatchUploadItem(
                    asset_id=asset_id,
                    make=make,
                    model=model,
                    serial_number=serial,
                    cpu=get_val(row, "cpu", "processor"),
                    ram_gb=ram_val,
                    storage_gb=storage_val,
                    reported_issues=issues,
                    battery_cycles=cycles_val,
                    battery_capacity_percent=cap_val,
                    cosmetic_condition=cosmetic,
                    org_id=org_id,
                )
            )

        return items, errors

    def create_job_record(
        self,
        items: List[BatchUploadItem],
        org_id: str = "default_org",
    ) -> str:
        job_id = f"batch_{uuid4().hex[:12]}"
        summary = BatchJobSummary(
            job_id=job_id,
            org_id=org_id,
            status="QUEUED",
            total_devices=len(items),
            processed_devices=0,
            successful_devices=0,
            failed_devices=0,
            pathway_counts={},
            devices=[],
            errors=[],
        )
        self.jobs[job_id] = summary
        self._raw_items[job_id] = items
        return job_id

    def process_batch_job_sync(
        self,
        job_id: str,
        items: List[BatchUploadItem],
        objective: Objective,
    ):
        summary = self.jobs[job_id]
        summary.status = "PROCESSING"
        from concurrent.futures import ThreadPoolExecutor

        device_results: List[BatchDeviceResult] = []
        pathway_counts: Dict[str, int] = {}
        total_cost = 0.0
        total_carbon = 0.0
        successful = 0
        failed = 0

        max_workers = min(self.max_concurrency, max(1, len(items)))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._assess_device_sync, it, objective) for it in items]
            for f in futures:
                if job_id in self._cancel_flags:
                    break
                try:
                    r = f.result()
                    device_results.append(r)
                    summary.processed_devices += 1
                    if r.status == "SUCCESS":
                        successful += 1
                        pw = r.primary_pathway or "UNKNOWN"
                        pathway_counts[pw] = pathway_counts.get(pw, 0) + 1
                        total_cost += r.estimated_cost_inr or 0.0
                        total_carbon += r.estimated_carbon_avoided_kg or 0.0
                    else:
                        failed += 1
                except Exception as ex:
                    failed += 1
                    summary.processed_devices += 1
                    device_results.append(
                        BatchDeviceResult(
                            asset_id="UNKNOWN",
                            product_id="",
                            model="Unknown",
                            status="FAILED",
                            error_message=str(ex),
                        )
                    )

        summary.devices = device_results
        summary.successful_devices = successful
        summary.failed_devices = failed
        summary.pathway_counts = pathway_counts
        summary.total_cost_inr = round(total_cost, 2)
        summary.total_carbon_avoided_kg = round(total_carbon, 2)
        summary.completed_at = datetime.now(timezone.utc).isoformat()
        summary.status = "CANCELLED" if job_id in self._cancel_flags else "COMPLETED"

    async def start_batch_job(
        self,
        items: List[BatchUploadItem],
        org_id: str = "default_org",
        user_objective: Objective = Objective.LOWEST_COST,
    ) -> str:
        """Initializes a new batch assessment job and begins background execution."""
        job_id = self.create_job_record(items, org_id)
        import threading
        t = threading.Thread(target=self.process_batch_job_sync, args=(job_id, items, user_objective), daemon=True)
        t.start()
        return job_id

    def _assess_device_sync(self, item: BatchUploadItem, objective: Objective) -> BatchDeviceResult:
        """Processes a single item through the condition synthesis and deterministic optimizer."""
        db = SessionLocal()
        try:
            prod_id = f"batch_prod_{uuid4().hex[:10]}"
            model_year = 2021
            age = max(0.5, float(2026 - model_year))
            product = ProductRecord(
                id=prod_id,
                manufacturer=item.make or "Generic",
                model=item.model,
                model_year=model_year,
                age=age,
                category=DeviceCategory.LAPTOP,
                serial_or_identifier=item.serial_number or item.asset_id,
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
            try:
                from app.db.repositories import product_repo, evidence_repo
                product_repo.save(db, product)
            except Exception:
                pass

            # Ingest Evidence
            # 1. Specs evidence
            ev_spec = EvidenceItem(
                product_id=prod_id,
                type=EvidenceType.DATABASE,
                source="enterprise_inventory_manifest",
                component="system",
                value={"model": item.model, "ram_gb": item.ram_gb, "storage_gb": item.storage_gb},
            )
            store.add_evidence(prod_id, ev_spec)

            # 2. Battery evidence if present
            if item.battery_capacity_percent is not None or item.battery_cycles is not None:
                cap = item.battery_capacity_percent or 85.0
                cycles = item.battery_cycles or 150
                ev_bat = EvidenceItem(
                    product_id=prod_id,
                    type=EvidenceType.DIAGNOSTIC,
                    source="inventory_battery_telemetry",
                    component="battery",
                    value={"health_percentage": cap, "cycle_count": cycles, "status": "GOOD" if cap >= 80 else "WEAR"},
                )
                store.add_evidence(prod_id, ev_bat)

            # 3. Reported issues
            if item.reported_issues:
                ev_iss = EvidenceItem(
                    product_id=prod_id,
                    type=EvidenceType.USER_REPORTED,
                    source="enterprise_it_ticket",
                    component="general",
                    value={"reported_issues": item.reported_issues},
                )
                store.add_evidence(prod_id, ev_iss)

            # 4. Cosmetic condition
            if item.cosmetic_condition:
                is_damaged = any(k in item.cosmetic_condition.lower() for k in ["crack", "broken", "dent"])
                ev_cos = EvidenceItem(
                    product_id=prod_id,
                    type=EvidenceType.VISUAL,
                    source="inventory_optical_check",
                    component="chassis",
                    value={
                        "observation": f"Chassis condition: {item.cosmetic_condition}",
                        "visible_status": "HIGH" if is_damaged else "GOOD",
                    },
                )
                store.add_evidence(prod_id, ev_cos)

            # Build profile
            profile = assessment_service.build_profile(prod_id, db=db)

            # Run deterministic circular optimizer (using deterministic template explanation for batch speed)
            req = RecommendationRequest(product_id=prod_id, objective=objective, skip_ai_explanation=True)
            rec = recommendation_service.generate_recommendation(req, db=db)

            pw_name = rec.selected_pathway.value if hasattr(rec.selected_pathway, "value") else str(rec.selected_pathway)
            cost_val = 3000.0
            carbon_val = 180.0
            life_val = 24.0

            if rec.primary_recommendation and hasattr(rec.primary_recommendation, "pathway"):
                pw = rec.primary_recommendation.pathway
                if hasattr(pw, "estimated_cost"):
                    c = pw.estimated_cost
                    cost_val = float(getattr(c, "value", getattr(c, "amount", 3000.0)))
                if hasattr(pw, "environmental_estimate"):
                    env = pw.environmental_estimate
                    carbon_val = float(getattr(env, "co2_avoided_kg_max", getattr(env, "value", 180.0)))
                if hasattr(pw, "expected_life_extension"):
                    life = pw.expected_life_extension
                    life_val = float(getattr(life, "value", getattr(life, "months", 24.0)))

            return BatchDeviceResult(
                asset_id=item.asset_id,
                product_id=prod_id,
                model=item.model,
                status="SUCCESS",
                primary_pathway=pw_name,
                primary_score=round(float(rec.score), 2) if rec.score else 85.0,
                estimated_cost_inr=round(cost_val, 2),
                estimated_carbon_avoided_kg=round(carbon_val, 2),
                extended_life_months=round(life_val, 1),
                condition_summary=f"Overall Health: {profile.overall_hardware_health}",
            )
        except Exception as e:
            logger.exception(f"Error assessing batch asset {item.asset_id}: {e}")
            return BatchDeviceResult(
                asset_id=item.asset_id,
                product_id="",
                model=item.model,
                status="FAILED",
                error_message=str(e),
            )
        finally:
            db.close()

    def get_job_summary(self, job_id: str) -> Optional[BatchJobSummary]:
        return self.jobs.get(job_id)

    def cancel_job(self, job_id: str) -> bool:
        if job_id in self.jobs and self.jobs[job_id].status in ["QUEUED", "PROCESSING"]:
            self._cancel_flags.add(job_id)
            self.jobs[job_id].status = "CANCELLED"
            return True
        return False

    async def retry_failed(self, job_id: str, objective: Objective = Objective.LOWEST_COST) -> bool:
        summary = self.jobs.get(job_id)
        if not summary or summary.status not in ["COMPLETED", "FAILED", "CANCELLED"]:
            return False

        failed_assets = {d.asset_id for d in summary.devices if d.status == "FAILED"}
        raw_items = self._raw_items.get(job_id, [])
        items_to_retry = [it for it in raw_items if it.asset_id in failed_assets]

        if not items_to_retry:
            return False

        if job_id in self._cancel_flags:
            self._cancel_flags.remove(job_id)

        import threading
        t = threading.Thread(target=self.process_batch_job_sync, args=(job_id, items_to_retry, objective), daemon=True)
        t.start()
        return True

    def export_csv(self, job_id: str) -> str:
        summary = self.get_job_summary(job_id)
        if not summary:
            raise ValueError(f"Job {job_id} not found")

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Asset ID", "Model", "Assessment Status", "Recommended Pathway",
            "Optimization Score", "Estimated Cost (INR)", "Carbon Avoided (kg CO2e)",
            "Extended Lifespan (Months)", "Condition Summary", "Error Message", "Processed At"
        ])

        for d in summary.devices:
            writer.writerow([
                d.asset_id, d.model, d.status, d.primary_pathway or "N/A",
                d.primary_score or "N/A", d.estimated_cost_inr or 0.0,
                d.estimated_carbon_avoided_kg or 0.0, d.extended_life_months or 0.0,
                d.condition_summary or "", d.error_message or "", d.processed_at
            ])
        return output.getvalue()

    def export_excel(self, job_id: str) -> bytes:
        summary = self.get_job_summary(job_id)
        if not summary:
            raise ValueError(f"Job {job_id} not found")

        wb = openpyxl.Workbook()
        
        # Sheet 1: Fleet Executive Summary
        ws_sum = wb.active
        ws_sum.title = "Fleet Summary"
        
        ws_sum.append(["ReLoop AI — Enterprise Fleet Lifecycle Assessment Report"])
        ws_sum.append([f"Job ID: {summary.job_id}", f"Organization: {summary.org_id}"])
        ws_sum.append([f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"])
        ws_sum.append([])
        
        ws_sum.append(["Metric", "Value"])
        ws_sum.append(["Total Devices Assessed", summary.total_devices])
        ws_sum.append(["Successfully Processed", summary.successful_devices])
        ws_sum.append(["Failed / Requires Review", summary.failed_devices])
        ws_sum.append(["Total Estimated Repair & Transition Cost", f"INR {summary.total_cost_inr:,.2f}"])
        ws_sum.append(["Total Embodied Carbon Avoided", f"{summary.total_carbon_avoided_kg:,.2f} kg CO2e"])
        ws_sum.append([])
        
        ws_sum.append(["Circular Pathway Distribution", "Device Count", "Percentage"])
        for pw, cnt in summary.pathway_counts.items():
            pct = (cnt / summary.successful_devices * 100) if summary.successful_devices > 0 else 0
            ws_sum.append([pw, cnt, f"{pct:.1f}%"])

        # Sheet 2: Detailed Device Inventory
        ws_dev = wb.create_sheet(title="Device Inventory")
        headers = [
            "Asset ID", "Model", "Status", "Recommended Pathway", "Score",
            "Cost (INR)", "Carbon Avoided (kg)", "Life Extension (Months)", "Condition Summary", "Notes"
        ]
        ws_dev.append(headers)

        header_fill = PatternFill(start_color="0F766E", end_color="0F766E", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

        for col_num in range(1, len(headers) + 1):
            cell = ws_dev.cell(row=1, column=col_num)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")

        for d in summary.devices:
            ws_dev.append([
                d.asset_id, d.model, d.status, d.primary_pathway or "N/A",
                d.primary_score if d.primary_score is not None else "N/A",
                d.estimated_cost_inr or 0.0, d.estimated_carbon_avoided_kg or 0.0,
                d.extended_life_months or 0.0, d.condition_summary or "", d.error_message or ""
            ])

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()


# Global singleton instance
batch_service = BatchAssessmentService()
