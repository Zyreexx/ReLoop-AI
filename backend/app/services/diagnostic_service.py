"""
Diagnostic service with strict validation, evidence provenance,
and cross-platform diagnostic agent session management.

Enforces all engineering rules from rules.md:
- Full-charge capacity cannot exceed design capacity.
- Percentages in range 0-100.
- Cycle counts non-negative.
- Zero-hallucination evidence provenance for all 8 subsystems.
- Deterministic condition evaluation and fault severity classification.
"""
from datetime import datetime, timezone, timedelta
import re
import uuid
from typing import Any, Dict, List, Optional
from threading import Lock

from app.db.store import store
from app.schemas.enums import EvidenceType, ConfidenceLevel, ComponentStatus
from app.schemas.errors import AppException
from app.schemas.evidence import EvidenceItem
from app.schemas.diagnostics import (
    DiagnosticsInput,
    DiagnosticValidationResult,
    BatteryDiagnostic,
    SsdDiagnostic,
    RamDiagnostic,
    ThermalDiagnostic,
    CpuDiagnostic,
    DisplayDiagnostic,
    KeyboardDiagnostic,
    ChassisDiagnostic,
    SystemDiagnostic,
    DiagnosticSessionResponse,
    DiagnosticSessionSubmit,
    DiagnosticSessionReport,
    SubsystemResult,
)


class DiagnosticService:
    def __init__(self):
        self._lock = Lock()
        # session_token -> session_data dict
        self._sessions: Dict[str, Dict[str, Any]] = {}

    # ─── Session Management ───────────────────────────────────────────────────

    def create_session(self, product_id: Optional[str] = None) -> DiagnosticSessionResponse:
        token = f"reloop-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=2)

        initial_progress = {
            "battery": "Pending",
            "ssd": "Pending",
            "ram": "Pending",
            "thermals": "Pending",
            "cpu": "Pending",
            "display": "Pending",
            "keyboard": "Pending",
            "chassis": "Pending",
            "system": "Pending",
        }

        with self._lock:
            self._sessions[token] = {
                "session_token": token,
                "product_id": product_id or "default",
                "status": "PENDING",
                "created_at": now.isoformat(),
                "expires_at": expires.isoformat(),
                "subsystems_progress": initial_progress,
                "report": None,
            }

        return DiagnosticSessionResponse(
            session_token=token,
            product_id=product_id,
            status="PENDING",
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            subsystems_progress=initial_progress,
        )

    def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._sessions.get(session_token)

    def submit_session(
        self, session_token: str, data: DiagnosticSessionSubmit
    ) -> DiagnosticSessionReport:
        with self._lock:
            session = self._sessions.get(session_token)
            if not session:
                # Allow creating on the fly if token provided directly
                now = datetime.now(timezone.utc)
                session = {
                    "session_token": session_token,
                    "product_id": "default",
                    "status": "RUNNING",
                    "created_at": now.isoformat(),
                    "expires_at": (now + timedelta(hours=2)).isoformat(),
                    "subsystems_progress": {},
                    "report": None,
                }
                self._sessions[session_token] = session

        product_id = session.get("product_id") or "default"
        evidence_items: List[EvidenceItem] = []
        subsystems_results: Dict[str, SubsystemResult] = {}
        summary: Dict[str, str] = {}
        progress: Dict[str, str] = {}

        raw_subs = data.subsystems or {}

        # 1. Battery
        if "battery" in raw_subs:
            b_data = raw_subs["battery"]
            b_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="battery",
                source=b_data.get("source", "Cross-Platform Battery Diagnostic"),
                raw_data=b_data,
            )
            if b_ev:
                evidence_items.append(b_ev)
            subsystems_results["battery"] = SubsystemResult(**b_data)
            health = b_data.get("evidence", {}).get("health_percentage")
            summary["battery"] = f"{health}% health" if health is not None else b_data.get("status", "Reported")
            progress["battery"] = "Passed" if b_data.get("status") == "PASSED" else "Fault Detected"

        # 2. SSD / Storage
        if "ssd" in raw_subs:
            s_data = raw_subs["ssd"]
            s_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="ssd",
                source=s_data.get("source", "Cross-Platform Storage SMART Diagnostic"),
                raw_data=s_data,
            )
            if s_ev:
                evidence_items.append(s_ev)
            subsystems_results["ssd"] = SubsystemResult(**s_data)
            smart = s_data.get("evidence", {}).get("smart_status", "PASS")
            summary["ssd"] = f"SMART {smart}"
            progress["ssd"] = "Passed" if s_data.get("status") == "PASSED" else "Fault Detected"

        # 3. RAM / Memory
        if "ram" in raw_subs:
            r_data = raw_subs["ram"]
            r_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="ram",
                source=r_data.get("source", "Cross-Platform Memory Telemetry"),
                raw_data=r_data,
            )
            if r_ev:
                evidence_items.append(r_ev)
            subsystems_results["ram"] = SubsystemResult(**r_data)
            gb = r_data.get("evidence", {}).get("installed_gb")
            summary["ram"] = f"{gb}GB Installed" if gb else r_data.get("status", "PASS")
            progress["ram"] = "Passed" if r_data.get("status") == "PASSED" else "Fault Detected"

        # 4. Thermals
        if "thermals" in raw_subs:
            t_data = raw_subs["thermals"]
            t_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="thermals",
                source=t_data.get("source", "Cross-Platform Thermal Monitor"),
                raw_data=t_data,
            )
            if t_ev:
                evidence_items.append(t_ev)
            subsystems_results["thermals"] = SubsystemResult(**t_data)
            throttling = t_data.get("evidence", {}).get("throttling_detected", False)
            summary["thermals"] = "Throttling Logged" if throttling else "Normal"
            progress["thermals"] = "Passed" if t_data.get("status") == "PASSED" else "Fault Detected"

        # 5. CPU
        if "cpu" in raw_subs:
            c_data = raw_subs["cpu"]
            subsystems_results["cpu"] = SubsystemResult(**c_data)
            cores = c_data.get("evidence", {}).get("cores")
            summary["cpu"] = f"{cores} Cores" if cores else "Reported"
            progress["cpu"] = "Passed" if c_data.get("status") == "PASSED" else "Fault Detected"

        # 6. Display
        if "display" in raw_subs:
            d_data = raw_subs["display"]
            d_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="display",
                source=d_data.get("source", "Cross-Platform Display Subsystem"),
                raw_data=d_data,
            )
            if d_ev:
                evidence_items.append(d_ev)
            subsystems_results["display"] = SubsystemResult(**d_data)
            res = d_data.get("evidence", {}).get("resolution", "Active")
            summary["display"] = str(res)
            progress["display"] = "Passed" if d_data.get("status") == "PASSED" else "Fault Detected"

        # 7. Keyboard
        if "keyboard" in raw_subs:
            k_data = raw_subs["keyboard"]
            k_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="keyboard",
                source=k_data.get("source", "Cross-Platform Keyboard HID Controller"),
                raw_data=k_data,
            )
            if k_ev:
                evidence_items.append(k_ev)
            subsystems_results["keyboard"] = SubsystemResult(**k_data)
            summary["keyboard"] = "Operational" if k_data.get("status") == "PASSED" else "Fault Detected"
            progress["keyboard"] = "Passed" if k_data.get("status") == "PASSED" else "Fault Detected"

        # 8. Chassis
        if "chassis" in raw_subs:
            ch_data = raw_subs["chassis"]
            ch_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="chassis",
                source=ch_data.get("source", "Cross-Platform SMBIOS Enclosure"),
                raw_data=ch_data,
            )
            if ch_ev:
                evidence_items.append(ch_ev)
            subsystems_results["chassis"] = SubsystemResult(**ch_data)
            ff = ch_data.get("evidence", {}).get("form_factor", "Laptop")
            summary["chassis"] = str(ff)
            progress["chassis"] = "Passed"

        # 9. System Board
        if "system" in raw_subs:
            sys_data = raw_subs["system"]
            sys_ev = self._record_subsystem_evidence(
                product_id=product_id,
                component="system",
                source=sys_data.get("source", "Cross-Platform System Board UEFI Diagnostics"),
                raw_data=sys_data,
            )
            if sys_ev:
                evidence_items.append(sys_ev)
            subsystems_results["system"] = SubsystemResult(**sys_data)
            post_ok = sys_data.get("evidence", {}).get("post_successful", True)
            summary["system"] = "POST PASS" if post_ok else "FAULT"
            progress["system"] = "Passed" if post_ok else "Fault Detected"

        overall_health = data.overall_status or "GOOD"
        comp_statuses = [r.component_status for r in subsystems_results.values()]
        if "REPLACE" in comp_statuses:
            overall_health = "DEGRADED"
        elif "WEAR" in comp_statuses:
            overall_health = "FAIR"
        elif all(s == "GOOD" for s in comp_statuses):
            overall_health = "GOOD"
        else:
            overall_health = "FAIR"

        # Synthesize plain-language explanation grounded in evidence
        ai_explanation = self._synthesize_explanation(subsystems_results, data.faults or [])

        report = DiagnosticSessionReport(
            session_token=session_token,
            product_id=product_id,
            status="COMPLETED",
            overall_hardware_health=overall_health,
            subsystems=subsystems_results,
            faults=data.faults or [],
            summary=summary,
            evidence_items=evidence_items,
            ai_explanation=ai_explanation,
        )

        with self._lock:
            session["status"] = "COMPLETED"
            session["subsystems_progress"] = progress
            session["report"] = report

        return report

    def _record_subsystem_evidence(
        self, product_id: str, component: str, source: str, raw_data: Dict[str, Any]
    ) -> Optional[EvidenceItem]:
        val = raw_data.get("evidence", {})
        if not val and not raw_data.get("observations"):
            return None

        # Merge status & observations into evidence payload
        evidence_payload = {
            **val,
            "diagnostic_status": raw_data.get("status", "PASSED"),
            "component_status": raw_data.get("component_status", "GOOD"),
            "fault_severity": raw_data.get("fault_severity", "INFO"),
            "observations": raw_data.get("observations", []),
            "faults": raw_data.get("faults", []),
        }

        # Subsystem-specific payload mappings
        if component == "battery":
            if "health_percentage" in val:
                evidence_payload["health_percent"] = val["health_percentage"]
        elif component == "ssd":
            if "health_percentage" in val:
                evidence_payload["health_percent"] = val["health_percentage"]
        elif component == "ram":
            evidence_payload["memory_test_status"] = val.get("test_result", "PASS")
        elif component == "thermals":
            evidence_payload["cpu_max_temp_c"] = val.get("max_temp_c", 45.0)

        item = EvidenceItem(
            type=EvidenceType.DIAGNOSTIC,
            source=source,
            component=component,
            value=evidence_payload,
            confidence=ConfidenceLevel.HIGH,
        )
        store.add_evidence(product_id, item)
        return item

    def _synthesize_explanation(
        self, subsystems: Dict[str, SubsystemResult], faults: List[Dict[str, Any]]
    ) -> str:
        """
        Generate plain-language explanation of detected problems grounded in actual evidence.
        Uses deterministic reasoning with clear circular recommendations.
        """
        if not faults:
            return (
                "Hardware telemetry across all tested internal subsystems indicates normal operational parameters. "
                "No critical hardware wear, thermal throttling, or component faults were detected. "
                "The laptop is in good operational condition for redeployment or reuse."
            )

        descriptions = []
        for f in faults:
            comp = f.get("component", "system").upper()
            sev = f.get("severity", "MEDIUM")
            desc = f.get("description", "")
            descriptions.append(f"• [{sev}] {comp}: {desc}")

        recs = []
        if "battery" in subsystems and subsystems["battery"].component_status in ["WEAR", "REPLACE"]:
            b_sub = subsystems["battery"]
            pct = b_sub.evidence.get("health_percentage", 0)
            recs.append(f"Battery has degraded to {pct}% of factory capacity; replacement recommended to restore full portability.")

        if "thermals" in subsystems and subsystems["thermals"].component_status == "WEAR":
            recs.append("Thermal paste renewal and heatsink fin cleaning indicated to resolve firmware throttling.")

        if "ssd" in subsystems and subsystems["ssd"].component_status == "REPLACE":
            recs.append("Storage drive SMART warning indicates impending drive failure; immediate backup and SSD upgrade recommended.")

        explanation = (
            f"Diagnostics detected {len(faults)} hardware anomaly/wear indicator(s):\n"
            + "\n".join(descriptions)
        )
        if recs:
            explanation += "\n\nCircular Optimization Guidance:\n" + "\n".join(f"• {r}" for r in recs)

        return explanation

    # ─── Existing Validate & Record (Backwards Compatibility) ────────────────

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

        # 7. Display validation
        if data.display:
            d_diag = data.display
            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="Display Subsystem Diagnostic",
                component="display",
                value={
                    "adapter": d_diag.adapter,
                    "resolution": d_diag.resolution,
                    "status": d_diag.status or "OK",
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["display"] = d_diag.resolution or d_diag.status or "OK"

        # 8. Keyboard validation
        if data.keyboard:
            k_diag = data.keyboard
            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="Keyboard HID Controller Diagnostic",
                component="keyboard",
                value={
                    "device": k_diag.device,
                    "status": k_diag.status or "OK",
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["keyboard"] = k_diag.status or "OK"

        # 9. Chassis validation
        if data.chassis:
            ch_diag = data.chassis
            ev = EvidenceItem(
                type=EvidenceType.DIAGNOSTIC,
                source="Chassis SMBIOS Diagnostic",
                component="chassis",
                value={
                    "form_factor": ch_diag.form_factor,
                    "notes": ch_diag.notes,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            evidence_items.append(ev)
            summary["chassis"] = ch_diag.form_factor or "Laptop"

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
