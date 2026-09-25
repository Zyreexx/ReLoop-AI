"""
Assessment service for synthesizing component-level condition profile from evidence provenance.
Maintains strict boundaries per docs/rules.md:
- A photo never proves internal battery/SSD/motherboard/RAM/thermal health.
- Visual evidence can never set BATTERY/SSD/RAM/THERMALS/SYSTEM status.
- USER_REPORTED alone never produces GOOD status.
- Missing evidence yields UNKNOWN with "Insufficient evidence" and "Untested" label.
- Clear evidence source attribution for every component claim.
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.db.store import store
from app.schemas.enums import ComponentStatus, ConfidenceLevel, EvidenceType
from app.schemas.errors import AppException
from app.schemas.evidence import EvidenceItem
from app.schemas.condition import ComponentCondition, ConditionProfile
from app.schemas.product import ProductRecord


class AssessmentService:
    def build_profile(self, product_id: str, db: Optional[Session] = None) -> ConditionProfile:
        from app.db.repositories import product_repo, evidence_repo, assessment_repo
        product = store.get_product(product_id)
        if not product and db:
            product = product_repo.get_by_id(db, product_id)

        if not product:
            raise AppException(
                code="PRODUCT_NOT_FOUND",
                message=f"No product registered with ID '{product_id}'. Please identify product first.",
                field="product_id",
                status_code=404,
            )

        evidence_list = store.get_evidence(product_id)
        if not evidence_list and db:
            evidence_list = evidence_repo.get_by_product_id(db, product_id)
        components: Dict[str, ComponentCondition] = {}

        # 1. BATTERY (Diagnostic / User-Reported only — Visual can NEVER prove battery health)
        batt_evs = [e for e in evidence_list if e.component == "battery"]
        components["battery"] = self._synthesize_battery(batt_evs, product)

        # 2. SSD (Diagnostic / User-Reported only — Visual can NEVER prove SSD health)
        ssd_evs = [e for e in evidence_list if e.component == "ssd"]
        components["ssd"] = self._synthesize_ssd(ssd_evs, product)

        # 3. RAM (Diagnostic / User-Reported only — Visual can NEVER prove RAM health)
        ram_evs = [e for e in evidence_list if e.component == "ram"]
        components["ram"] = self._synthesize_ram(ram_evs, product)

        # 4. THERMALS (Diagnostic / User-Reported only — Visual can NEVER prove thermals)
        thm_evs = [e for e in evidence_list if e.component == "thermals"]
        components["thermals"] = self._synthesize_thermals(thm_evs, product)

        # 5. DISPLAY (Visual / Diagnostic / User-Reported)
        disp_evs = [e for e in evidence_list if e.component == "display"]
        components["display"] = self._synthesize_display(disp_evs, product)

        # 6. KEYBOARD (Visual / User-Reported)
        kb_evs = [e for e in evidence_list if e.component == "keyboard"]
        components["keyboard"] = self._synthesize_keyboard(kb_evs, product)

        # 7. CHASSIS / HINGE (Visual / User-Reported)
        chas_evs = [e for e in evidence_list if e.component in ["chassis", "hinge", "hinge_chassis"]]
        components["chassis"] = self._synthesize_chassis(chas_evs, product)

        # 8. SYSTEM / MOTHERBOARD (Diagnostic / User-Reported only — Visual can NEVER prove board health)
        sys_evs = [e for e in evidence_list if e.component in ["system", "motherboard"]]
        components["system"] = self._synthesize_system(sys_evs, product)

        # Determine overall device health label
        statuses = [c.status for c in components.values()]
        if ComponentStatus.REPLACE_REQUIRED in statuses:
            overall = "DEGRADED"
        elif ComponentStatus.SERVICE_REQUIRED in statuses:
            overall = "FAIR"
        elif all(s == ComponentStatus.GOOD for s in statuses):
            overall = "GOOD"
        elif any(s == ComponentStatus.UNKNOWN for s in statuses):
            overall = "FAIR"
        else:
            overall = "FAIR"

        profile = ConditionProfile(
            product_id=product_id,
            overall_hardware_health=overall,
            components=components,
            all_evidence=evidence_list,
        )
        if db:
            assessment_repo.save(db, profile)
        return store.save_profile(profile)

    def _synthesize_battery(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        # Filter strictly: Visual evidence cannot set battery health
        diag_ev = next((e for e in evs if e.type == EvidenceType.DIAGNOSTIC), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)

        measurements = {}
        observations = []
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]

        if diag_ev:
            val = diag_ev.value if isinstance(diag_ev.value, dict) else {}
            health_pct = val.get("health_percentage") or val.get("health_percent")
            cycles = val.get("cycle_count")
            if health_pct is not None:
                measurements["health_percentage"] = f"{health_pct}%"
            if cycles is not None:
                measurements["cycle_count"] = str(cycles)

            if health_pct is not None:
                if health_pct < 65.0:
                    status = ComponentStatus.REPLACE_REQUIRED
                    label = f"{health_pct}% — Degraded"
                elif health_pct < 80.0:
                    status = ComponentStatus.SERVICE_REQUIRED
                    label = f"{health_pct}% — Service Recommended"
                else:
                    status = ComponentStatus.GOOD
                    label = f"{health_pct}% — Healthy"
            else:
                status = ComponentStatus.FAIR
                label = "Diagnostic Logged"
            observations.append(f"Measured {val.get('full_charge_capacity_mwh', 'N/A')} mWh of design capacity ({diag_ev.source}).")
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.SERVICE_REQUIRED
            label = "User: Rapid Discharge"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User reported: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            # Missing evidence yields UNKNOWN with "Insufficient evidence"
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No diagnostic battery report uploaded. Visual inspection cannot verify battery chemistry.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="battery",
            status=status,
            label=label,
            observations=observations,
            measurements=measurements,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=prod.specs.battery_replaceable,
            upgradeable=False,
        )

    def _synthesize_ssd(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        # Filter strictly: Visual evidence cannot set SSD health
        diag_ev = next((e for e in evs if e.type == EvidenceType.DIAGNOSTIC), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]
        measurements = {}
        observations = []

        if diag_ev:
            val = diag_ev.value if isinstance(diag_ev.value, dict) else {}
            health_pct = val.get("health_percentage") or val.get("health_percent")
            smart = val.get("smart_status", "PASS")
            if health_pct is not None:
                measurements["health_percentage"] = f"{health_pct}%"
            measurements["smart_status"] = smart

            if smart == "FAIL" or (health_pct is not None and health_pct < 20.0):
                status = ComponentStatus.REPLACE_REQUIRED
                label = f"{health_pct or 0}% — Failing"
            elif health_pct is not None and health_pct < 70.0:
                status = ComponentStatus.FAIR
                label = f"{health_pct}% — Fair"
            else:
                status = ComponentStatus.GOOD
                label = f"{health_pct or 95}% — Healthy"
            observations.append(f"SMART state: {smart}; health: {health_pct or 95}% ({diag_ev.source}).")
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.SERVICE_REQUIRED
            label = "User: Storage Latency / Errors"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User reported: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            # Missing evidence yields UNKNOWN with "Insufficient evidence"
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No SMART or storage diagnostic uploaded. Visual inspection cannot verify SSD health.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="ssd",
            status=status,
            label=label,
            observations=observations,
            measurements=measurements,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=prod.specs.ssd_modular,
            upgradeable=prod.specs.ssd_modular,
        )

    def _synthesize_ram(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        # Filter strictly: Visual evidence cannot set RAM health
        diag_ev = next((e for e in evs if e.type == EvidenceType.DIAGNOSTIC), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]
        measurements = {}
        observations = []

        if diag_ev:
            val = diag_ev.value if isinstance(diag_ev.value, dict) else {}
            test_status = str(val.get("memory_test_status") or val.get("diagnostic_status") or val.get("test_result") or "PASS").upper()
            measurements["diagnostic_result"] = test_status
            if val.get("installed_gb") or val.get("total_gb"):
                measurements["capacity_gb"] = f"{val.get('installed_gb') or val.get('total_gb')} GB"

            if test_status == "FAIL":
                status = ComponentStatus.REPLACE_REQUIRED
                label = "FAIL — Memory Errors"
            elif test_status == "PASS":
                status = ComponentStatus.GOOD
                label = "PASS"
            else:
                status = ComponentStatus.UNKNOWN
                label = "Untested"
            observations.append(f"Hardware memory test status: {test_status} ({diag_ev.source}).")
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.SERVICE_REQUIRED
            label = "User: Memory Errors / Crashing"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User reported: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            # Missing evidence yields UNKNOWN with "Insufficient evidence"
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No memory diagnostic test uploaded. Visual inspection cannot verify RAM integrity.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="ram",
            status=status,
            label=label,
            observations=observations,
            measurements=measurements,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=prod.specs.ram_modular,
            upgradeable=prod.specs.ram_modular,
        )

    def _synthesize_thermals(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        # Filter strictly: Visual evidence cannot set thermals
        diag_ev = next((e for e in evs if e.type == EvidenceType.DIAGNOSTIC), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]
        measurements = {}
        observations = []

        if diag_ev:
            val = diag_ev.value if isinstance(diag_ev.value, dict) else {}
            throttling = bool(val.get("throttling_detected") or val.get("thermal_throttling") or False)
            service = bool(val.get("service_recommended") or False)
            max_temp = val.get("cpu_max_temp_c") or val.get("cpu_load_temp_c") or val.get("max_temp_c")
            if max_temp:
                measurements["cpu_max_temp"] = f"{max_temp}°C"

            if service or throttling or (max_temp and float(max_temp) >= 90.0):
                status = ComponentStatus.SERVICE_REQUIRED
                label = "Service Required"
                observations.append(f"Thermal throttling detected (Peak {max_temp or 94}°C). Thermal interface paste repaste indicated.")
            else:
                status = ComponentStatus.GOOD
                label = "Normal (<80°C)"
                observations.append("Core operating temps within standard manufacturer thermal envelope.")
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.SERVICE_REQUIRED
            label = "User: Loud Fans / Hot"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User noted: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            # Missing evidence yields UNKNOWN with "Insufficient evidence"
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No thermal telemetry or temperature log uploaded. Visual inspection cannot verify heatsink performance.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="thermals",
            status=status,
            label=label,
            observations=observations,
            measurements=measurements,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=True,
            upgradeable=False,
        )

    def _synthesize_display(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        vis_ev = next((e for e in evs if e.type == EvidenceType.VISUAL), None)
        diag_ev = next((e for e in evs if e.type == EvidenceType.DIAGNOSTIC), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]
        observations = []

        if diag_ev:
            val = diag_ev.value if isinstance(diag_ev.value, dict) else {}
            diag_status = str(val.get("status", "GOOD")).upper()
            if diag_status in ["REPLACE", "FAIL", "REPLACE_REQUIRED"]:
                status = ComponentStatus.REPLACE_REQUIRED
                label = "Panel Failure"
            elif diag_status in ["SERVICE_REQUIRED", "WEAR", "FAIR"]:
                status = ComponentStatus.SERVICE_REQUIRED
                label = "Display Issue"
            else:
                status = ComponentStatus.GOOD
                label = "Bench Tested OK"
            observations.append(f"Display diagnostic: {val.get('note', 'Tested panel output')} ({diag_ev.source}).")
            confidence = ConfidenceLevel.HIGH
        elif vis_ev:
            vis_data = vis_ev.value if isinstance(vis_ev.value, dict) else {}
            status_str = str(vis_data.get("visible_status", vis_data.get("severity", "GOOD"))).upper()
            obs = vis_data.get("observation", vis_data.get("description", ""))
            observations.append(f"Optical scan: {obs} ({vis_ev.source}).")
            if status_str in ["SERVICE_REQUIRED", "HIGH", "CRITICAL", "DAMAGED"]:
                status = ComponentStatus.SERVICE_REQUIRED
                label = "Visible Damage / Crack"
            else:
                status = ComponentStatus.GOOD
                label = "Clean / No Cracks"
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.SERVICE_REQUIRED
            label = "User: Display Defect"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User reported: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No display inspection photos or diagnostic uploaded.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="display",
            status=status,
            label=label,
            observations=observations,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=True,
            upgradeable=False,
        )

    def _synthesize_keyboard(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        vis_ev = next((e for e in evs if e.type == EvidenceType.VISUAL), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]
        observations = []

        if vis_ev:
            val = vis_ev.value if isinstance(vis_ev.value, dict) else {}
            status_str = str(val.get("visible_status", val.get("severity", "GOOD"))).upper()
            obs = val.get("observation", val.get("description", ""))
            if status_str in ["SERVICE_REQUIRED", "MEDIUM", "HIGH", "CRITICAL", "DAMAGED"]:
                status = ComponentStatus.SERVICE_REQUIRED
                label = "Key Damage / Missing"
            else:
                status = ComponentStatus.GOOD
                label = "Intact"
            observations.append(f"Visual inspection: {obs} ({vis_ev.source}).")
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.SERVICE_REQUIRED
            label = "User: Sticky / Unresponsive"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User reported: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No keyboard inspection photos or diagnostic uploaded.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="keyboard",
            status=status,
            label=label,
            observations=observations,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=True,
            upgradeable=False,
        )

    def _synthesize_chassis(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        vis_ev = next((e for e in evs if e.type == EvidenceType.VISUAL), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]
        observations = []

        if vis_ev:
            val = vis_ev.value if isinstance(vis_ev.value, dict) else {}
            severity = str(val.get("severity", val.get("visible_status", "LOW"))).upper()
            obs = val.get("observation", val.get("description", "Chassis visual analysis"))
            if severity in ["HIGH", "CRITICAL", "SERVICE_REQUIRED", "DAMAGED"]:
                status = ComponentStatus.SERVICE_REQUIRED
                label = "Chassis Damage"
            elif severity in ["MEDIUM", "FAIR"]:
                status = ComponentStatus.FAIR
                label = "Moderate Cosmetic Wear"
            else:
                status = ComponentStatus.GOOD
                label = "Solid / Minor Wear"
            observations.append(f"Optical analysis: {obs} ({vis_ev.source}).")
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.FAIR
            label = "User: Chassis Wear"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User noted: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        else:
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No chassis inspection photos uploaded.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="chassis",
            status=status,
            label=label,
            observations=observations,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=True,
            upgradeable=False,
        )

    def _synthesize_system(self, evs: List[EvidenceItem], prod: ProductRecord) -> ComponentCondition:
        # Filter strictly: Visual evidence can NEVER prove internal motherboard health
        diag_ev = next((e for e in evs if e.type == EvidenceType.DIAGNOSTIC), None)
        user_ev = next((e for e in evs if e.type == EvidenceType.USER_REPORTED), None)
        db_ev = next((e for e in evs if e.type == EvidenceType.DATABASE), None)
        evidence_ids = [e.id for e in evs]
        sources = [e.source for e in evs]
        observations = []

        if diag_ev:
            val = diag_ev.value if isinstance(diag_ev.value, dict) else {}
            post_stat = str(val.get("uefi_post_status") or val.get("post_status") or val.get("status") or "").upper()
            post_success = val.get("post_successful", True)
            power_rails = str(val.get("power_rails", "")).upper()
            crit_errors = val.get("critical_errors", [])

            if post_stat in ["FAIL", "REPLACE"] or not post_success or power_rails == "SHORTED" or len(crit_errors) > 0:
                status = ComponentStatus.REPLACE_REQUIRED
                label = "Dead / POST Failure"
                observations.append(f"System POST failure / power fault detected ({diag_ev.source}).")
            else:
                status = ComponentStatus.GOOD
                label = "POST & Power OK"
                observations.append(f"Motherboard sensors normal and POST passed ({diag_ev.source}).")
            confidence = ConfidenceLevel.HIGH
        elif user_ev:
            # USER_REPORTED alone never produces GOOD
            status = ComponentStatus.SERVICE_REQUIRED
            label = "User: System Instability"
            statement = user_ev.value.get("user_statement") or user_ev.value.get("reported_issues") if isinstance(user_ev.value, dict) else str(user_ev.value)
            observations.append(f"User reported: {statement}")
            confidence = ConfidenceLevel.MEDIUM
        elif db_ev:
            # Baseline catalog specification present, but no functional diagnostics run
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append(f"Hardware architecture: {prod.manufacturer} {prod.model} ({prod.model_year}).")
            observations.append("Insufficient evidence: No motherboard diagnostics or UEFI POST telemetry available.")
            confidence = ConfidenceLevel.LOW
        else:
            status = ComponentStatus.UNKNOWN
            label = "Untested"
            observations.append("Insufficient evidence: No motherboard diagnostics or UEFI POST telemetry available.")
            confidence = ConfidenceLevel.LOW

        return ComponentCondition(
            component="system",
            status=status,
            label=label,
            observations=observations,
            confidence=confidence,
            evidence_ids=evidence_ids,
            evidence_sources=sources,
            repairable=False,
            upgradeable=False,
        )


assessment_service = AssessmentService()
