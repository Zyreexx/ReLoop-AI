"""
Diagnostic service with strict validation and evidence provenance.
Enforces all engineering rules from rules.md:
- Full-charge capacity cannot exceed design capacity.
- Percentages in range 0-100.
- Cycle counts non-negative.
"""
import re
from typing import List, Optional
from app.db.store import store
from app.schemas.enums import EvidenceType, ConfidenceLevel
from app.schemas.errors import AppException
from app.schemas.evidence import EvidenceItem
from app.schemas.diagnostics import (
    DiagnosticsInput,
    DiagnosticValidationResult,
    BatteryDiagnostic,
    SsdDiagnostic,
    RamDiagnostic,
    ThermalDiagnostic,
)


class DiagnosticService:
    def validate_and_record(self, data: DiagnosticsInput) -> DiagnosticValidationResult:
        product_id = data.product_id or "default"
        evidence_items: List[EvidenceItem] = []
        summary: dict = {}

        # 1. Parse text report if provided (e.g. Windows powercfg /batteryreport or SMART log)
        if data.report_text:
            parsed_batt, parsed_ssd = self._parse_report_text(data.report_text)
            if parsed_batt and not data.battery:
                data.battery = parsed_batt
            if parsed_ssd and not data.ssd:
                data.ssd = parsed_ssd

        # 2. Battery validation
        if data.battery:
            batt = data.battery
            if (
                batt.design_capacity_mwh is not None
                and batt.full_charge_capacity_mwh is not None
            ):
                if batt.full_charge_capacity_mwh > batt.design_capacity_mwh:
                    raise AppException(
                        code="INVALID_DIAGNOSTIC",
                        message="Full-charge capacity cannot exceed design capacity.",
                        field="battery.full_charge_capacity",
                        status_code=400,
                    )
                if batt.health_percentage is None and batt.design_capacity_mwh > 0:
                    batt.health_percentage = round(
                        (batt.full_charge_capacity_mwh / batt.design_capacity_mwh) * 100.0, 1
                    )

            if batt.cycle_count is not None and batt.cycle_count < 0:
                raise AppException(
                    code="INVALID_DIAGNOSTIC",
                    message="Cycle count cannot be negative.",
                    field="battery.cycle_count",
                    status_code=400,
                )

            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="OS Battery Diagnostic Report",
                component="battery",
                value={
                    "design_capacity_mwh": batt.design_capacity_mwh,
                    "full_charge_capacity_mwh": batt.full_charge_capacity_mwh,
                    "cycle_count": batt.cycle_count,
                    "health_percentage": batt.health_percentage,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["battery"] = f"{batt.health_percentage}% health" if batt.health_percentage is not None else "Reported"

        # 3. SSD validation
        if data.ssd:
            ssd = data.ssd
            if ssd.health_percentage is not None and not (0.0 <= ssd.health_percentage <= 100.0):
                raise AppException(
                    code="INVALID_DIAGNOSTIC",
                    message="SSD health percentage must be between 0 and 100.",
                    field="ssd.health_percentage",
                    status_code=400,
                )

            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="Storage Controller SMART Diagnostic",
                component="ssd",
                value={
                    "smart_status": ssd.smart_status,
                    "health_percentage": ssd.health_percentage,
                    "power_on_hours": ssd.power_on_hours,
                    "total_bytes_written_tb": ssd.total_bytes_written_tb,
                    "capacity_gb": ssd.capacity_gb,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["ssd"] = f"{ssd.health_percentage}% SMART health" if ssd.health_percentage is not None else ssd.smart_status

        # 4. RAM validation
        if data.ram:
            ram = data.ram
            status_val = str(ram.memory_test_status or ram.test_result or "PASS").upper()
            if status_val not in ["PASS", "FAIL", "UNKNOWN"]:
                raise AppException(
                    code="INVALID_DIAGNOSTIC",
                    message="Memory diagnostic status must be PASS, FAIL, or UNKNOWN.",
                    field="ram.memory_test_status",
                    status_code=400,
                )

            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="UEFI / MemTest Hardware Diagnostic",
                component="ram",
                value={
                    "memory_test_status": status_val,
                    "installed_gb": ram.installed_gb,
                    "slots_used": ram.slots_used,
                    "total_slots": ram.total_slots,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["ram"] = f"{status_val} ({ram.installed_gb}GB)" if ram.installed_gb else status_val

        # 5. Thermals validation
        if data.thermals:
            thm = data.thermals
            if thm.cpu_idle_temp_c is not None and thm.cpu_max_temp_c is not None:
                if thm.cpu_idle_temp_c > thm.cpu_max_temp_c:
                    raise AppException(
                        code="INVALID_DIAGNOSTIC",
                        message="Idle CPU temperature cannot exceed max recorded temperature.",
                        field="thermals.cpu_idle_temp_c",
                        status_code=400,
                    )

            throttling = bool(thm.throttling_detected or (thm.cpu_max_temp_c and thm.cpu_max_temp_c >= 92.0))
            service_needed = thm.service_recommended if thm.service_recommended is not None else throttling

            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="Thermal Monitoring Log / HWInfo",
                component="thermals",
                value={
                    "cpu_idle_temp_c": thm.cpu_idle_temp_c,
                    "cpu_max_temp_c": thm.cpu_max_temp_c,
                    "throttling_detected": throttling,
                    "fan_noise_abnormal": thm.fan_noise_abnormal,
                    "service_recommended": service_needed,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["thermals"] = "Service Required" if service_needed else "Normal"

        # 6. System / Motherboard validation
        if data.system:
            sys_diag = data.system
            post_pass = sys_diag.post_successful
            power_ok = sys_diag.motherboard_power_stable
            critical = sys_diag.critical_errors or []
            status_val = "PASS" if (post_pass and power_ok and not critical) else "FAIL"

            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="UEFI POST / Motherboard Power Diagnostic",
                component="system",
                value={
                    "post_successful": post_pass,
                    "motherboard_power_stable": power_ok,
                    "critical_errors": critical,
                    "uefi_post_status": "PASS" if post_pass else "FAIL",
                    "power_rails": "NORMAL" if power_ok else "SHORTED",
                    "status": "GOOD" if post_pass and power_ok else "REPLACE",
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["system"] = status_val

        return DiagnosticValidationResult(
            valid=True,
            evidence_items=evidence_items,
            summary=summary,
        )

    def _parse_report_text(self, text: str) -> tuple[Optional[BatteryDiagnostic], Optional[SsdDiagnostic]]:
        batt = None
        ssd = None

        # Look for Windows battery report patterns
        design_match = re.search(r"DESIGN CAPACITY\s+([\d,]+)\s+mWh", text, re.IGNORECASE)
        full_match = re.search(r"FULL CHARGE CAPACITY\s+([\d,]+)\s+mWh", text, re.IGNORECASE)
        cycle_match = re.search(r"CYCLE COUNT\s+(\d+)", text, re.IGNORECASE)

        if design_match and full_match:
            design_cap = float(design_match.group(1).replace(",", ""))
            full_cap = float(full_match.group(1).replace(",", ""))
            cycles = int(cycle_match.group(1)) if cycle_match else None
            # Safeguard if full > design due to report anomalies
            if full_cap <= design_cap:
                batt = BatteryDiagnostic(
                    design_capacity_mwh=design_cap,
                    full_charge_capacity_mwh=full_cap,
                    cycle_count=cycles,
                )

        # Look for SMART patterns
        smart_health_match = re.search(r"(?:Percentage Used|SMART Health|Drive Remaining):\s*(\d+)%", text, re.IGNORECASE)
        if smart_health_match:
            pct_val = float(smart_health_match.group(1))
            ssd = SsdDiagnostic(
                smart_status="PASS",
                health_percentage=pct_val if pct_val <= 100 else 100.0 - pct_val,
            )

        return batt, ssd


diagnostic_service = DiagnosticService()
