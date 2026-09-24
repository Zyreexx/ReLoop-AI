"""
Vision service for product identification and optical visible damage assessment.
Enforces non-negotiable rules:
- Supported model list supplied to prompt
- needs_confirmation=True always for MVP
- UNSUPPORTED_MODEL response lets user select model manually
- Post-filter strictly drops any findings regarding internal component health (battery/SSD/RAM/motherboard)
- AI failure raises AppError AI_FAILURE
- Results persisted as VISUAL evidence records linked to product
"""
import re
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.ai.gemini_client import gemini_client
from app.ai.prompt_loader import load_prompt
from app.ai.schemas import ModelIdentificationOutput, DamageAssessmentOutput
from app.db.repositories import product_repo, evidence_repo
from app.db.store import store
from app.errors import AppError, ErrorCode
from app.knowledge.models_catalog import get_all_models, lookup_model
from app.schemas.enums import ComponentName, ComponentStatus, ConfidenceLevel, EvidenceType
from app.schemas.evidence import Evidence
from app.schemas.product import ProductCandidate, ProductIdentifyResponse, ProductSpecs
from app.schemas.vision import VisibleFinding, VisionAnalyzeResponse

# Keywords indicating internal hardware health that are strictly forbidden from visual reports
FORBIDDEN_INTERNAL_KEYWORDS = [
    "battery",
    "ssd",
    "storage",
    "nvme",
    "drive",
    "hard drive",
    "ram",
    "memory",
    "motherboard",
    "logic board",
    "mainboard",
    "circuit",
    "power rail",
    "cpu health",
    "silicon",
]


def filter_visible_findings(findings: List[VisibleFinding]) -> List[VisibleFinding]:
    """
    POST-FILTER: Strictly drops any finding claiming internal component health.
    A photo can NEVER prove internal battery, SSD, RAM, or motherboard health.
    Exception: visible battery swelling (exterior chassis deformation) is reported under HINGE_CHASSIS.
    """
    filtered = []
    for f in findings:
        comp_str = str(getattr(f.component, "value", f.component)).upper()
        desc_lower = f.description.lower()

        # If component is an internal hardware subsystem, drop it immediately
        if comp_str in ["BATTERY", "SSD", "RAM", "SYSTEM", "MOTHERBOARD"]:
            # Only allow if it describes visible exterior swelling deforming chassis
            if "swelling" in desc_lower or "bulge" in desc_lower or "bulging" in desc_lower:
                f.component = ComponentName.HINGE_CHASSIS
                filtered.append(f)
            continue

        # If description makes claims about internal electronic health, drop it
        if any(kw in desc_lower for kw in FORBIDDEN_INTERNAL_KEYWORDS):
            if not ("swelling" in desc_lower or "bulge" in desc_lower):
                continue

        filtered.append(f)

    return filtered


class VisionService:
    def identify(
        self,
        image_bytes_list: Optional[List[bytes]] = None,
        manual_model: Optional[str] = None,
        model_id: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> ProductIdentifyResponse:
        """
        Identifies model from images or direct manual model_id.
        Always sets needs_confirmation=True for MVP.
        Returns unsupported response if unknown.
        """
        all_supported = get_all_models()

        # 1. Manual path: client sends manual_model or model_id directly
        target_model = manual_model or model_id or hint
        if target_model and not image_bytes_list:
            matched = lookup_model(target_model)
            if matched:
                cand = ProductCandidate(
                    manufacturer=matched["manufacturer"],
                    model=matched["model"],
                    model_year=matched["model_year"],
                    confidence=ConfidenceLevel.HIGH,
                    specs=matched["specs"],
                )
                return ProductIdentifyResponse(
                    identified_model=cand,
                    is_supported=True,
                    confidence=1.0,
                    needs_confirmation=True,
                    requires_user_confirmation=True,
                    visual_clues=["Manually confirmed by user"],
                    supported_models=all_supported,
                )
            else:
                # Unsupported manual model
                return ProductIdentifyResponse(
                    identified_model=None,
                    is_supported=False,
                    confidence=0.0,
                    needs_confirmation=True,
                    requires_user_confirmation=True,
                    supported_models=all_supported,
                    message=f"Model '{target_model}' is not in the supported catalog. Please select a supported model.",
                )

        # 2. Vision path with Gemini
        supported_str = "\n".join([f"- {m.manufacturer} {m.model}" for m in all_supported])
        prompt_obj = load_prompt("vision_identify", "v1")
        prompt_text = prompt_obj.format(supported_models=supported_str)
        if hint:
            prompt_text += f"\nUser hint: {hint}"

        # Call Gemini (raises AppError AI_FAILURE on failure)
        ai_res: ModelIdentificationOutput = gemini_client.generate_structured(
            prompt=prompt_text,
            response_model=ModelIdentificationOutput,
            images=image_bytes_list,
        )

        matched_data = lookup_model(ai_res.model_name)
        if not matched_data or ai_res.model_name.lower() == "unknown":
            # Model unknown or unsupported: return response letting user pick manually
            return ProductIdentifyResponse(
                identified_model=None,
                is_supported=False,
                confidence=ai_res.confidence,
                visible_label_text=ai_res.visible_label_text,
                visual_clues=ai_res.visual_clues,
                needs_confirmation=True,
                requires_user_confirmation=True,
                supported_models=all_supported,
                message="Device model could not be verified from photos. Please select your device model manually.",
            )

        candidate = ProductCandidate(
            manufacturer=matched_data["manufacturer"],
            model=matched_data["model"],
            model_year=matched_data["model_year"],
            confidence=ConfidenceLevel.HIGH if ai_res.confidence >= 0.8 else ConfidenceLevel.MEDIUM,
            specs=matched_data["specs"],
        )

        alternatives = [
            m for m in all_supported
            if not (m.manufacturer == candidate.manufacturer and m.model == candidate.model)
        ][:3]

        return ProductIdentifyResponse(
            identified_model=candidate,
            is_supported=True,
            confidence=ai_res.confidence,
            visible_label_text=ai_res.visible_label_text,
            visual_clues=ai_res.visual_clues,
            needs_confirmation=True,
            requires_user_confirmation=True,
            alternative_models=alternatives,
            supported_models=all_supported,
        )

    def analyze(
        self,
        product_id: str,
        image_bytes_list: Optional[List[bytes]] = None,
        inspection_notes: Optional[str] = None,
        image_names: Optional[List[str]] = None,
        db: Optional[Session] = None,
    ) -> VisionAnalyzeResponse:
        """
        Analyzes visible exterior damage, post-filters internal claims,
        and saves results as VISUAL evidence items.
        """
        product = store.get_product(product_id)
        if not product and db:
            product = product_repo.get(db, product_id)

        if not product:
            raise AppError(
                code=ErrorCode.NOT_FOUND.value,
                message=f"No product registered with ID '{product_id}'",
                field="product_id",
                http_status=404,
            )

        raw_findings: List[VisibleFinding] = []

        if image_bytes_list:
            prompt_obj = load_prompt("vision_damage", "v1")
            prompt_text = prompt_obj.content
            if inspection_notes:
                prompt_text += f"\nInspection context from user: {inspection_notes}"

            ai_res: DamageAssessmentOutput = gemini_client.generate_structured(
                prompt=prompt_text,
                response_model=DamageAssessmentOutput,
                images=image_bytes_list,
            )

            # Map raw AI items to VisibleFinding
            for crack in ai_res.cracks:
                raw_findings.append(VisibleFinding(component=ComponentName.DISPLAY, description=crack, severity="HIGH"))
            for dent in ai_res.dents:
                raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=dent, severity="LOW"))
            for key in ai_res.missing_keys:
                raw_findings.append(VisibleFinding(component=ComponentName.KEYBOARD, description=key, severity="MODERATE"))
            for h_dmg in ai_res.hinge_damage:
                raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=h_dmg, severity="HIGH"))
            for p_dmg in ai_res.port_damage:
                raw_findings.append(VisibleFinding(component="PORTS", description=p_dmg, severity="MODERATE"))
            for swell in ai_res.visible_swelling:
                raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=f"Visible exterior bulge: {swell}", severity="HIGH"))
            for obs in ai_res.observations:
                raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description=obs, severity="LOW"))
        elif inspection_notes:
            # Fallback when only notes provided without images
            lowered = inspection_notes.lower()
            if "screen" in lowered or "crack" in lowered:
                raw_findings.append(VisibleFinding(component=ComponentName.DISPLAY, description=inspection_notes, severity="HIGH"))
            if "key" in lowered:
                raw_findings.append(VisibleFinding(component=ComponentName.KEYBOARD, description=inspection_notes, severity="MODERATE"))
            if not raw_findings:
                raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description="Exterior inspected; normal wear observed.", severity="LOW"))
        else:
            raw_findings.append(VisibleFinding(component=ComponentName.HINGE_CHASSIS, description="No visible physical damage detected.", severity="LOW"))

        # POST-FILTER: drop any claim about internal component health
        clean_findings = filter_visible_findings(raw_findings)

        # Save as VISUAL Evidence records linked to the product
        source_label = f"Optical Inspection ({', '.join(image_names) if image_names else 'Uploaded photos'})"
        evidence_items: List[Evidence] = []

        for f in clean_findings:
            ev = Evidence(
                type=EvidenceType.VISUAL,
                source=source_label,
                component=str(getattr(f.component, "value", f.component)).lower(),
                value={
                    "observation": f.description,
                    "severity": f.severity,
                    "confidence": f.confidence,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            store.add_evidence(product_id, ev)
            if db:
                try:
                    evidence_repo.add(db, ev, product_id=product_id)
                except Exception:
                    pass
            evidence_items.append(ev)

        # Determine overall condition
        has_severe = any(f.severity == "HIGH" for f in clean_findings)
        has_moderate = any(f.severity == "MODERATE" for f in clean_findings)
        overall_cond = ComponentStatus.DAMAGED if has_severe else (ComponentStatus.WEAR if has_moderate else ComponentStatus.GOOD)

        return VisionAnalyzeResponse(
            product_id=product_id,
            findings=clean_findings,
            overall_visual_condition="SERVICE_REQUIRED" if (has_severe or has_moderate) else "GOOD",
            overall_condition=overall_cond,
            evidence_items=evidence_items,
        )

    def analyze_visible_damage(
        self,
        req: VisionAnalyzeRequest,
        db: Optional[Session] = None,
    ) -> VisionAnalyzeResponse:
        return self.analyze(
            product_id=req.product_id,
            image_bytes_list=None,
            inspection_notes=req.inspection_notes,
            image_names=req.image_names,
            db=db,
        )


vision_service = VisionService()

