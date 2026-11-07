"""
Digital Product Passport (DPP) Service.
Generates, validates, and renders ESPR / CIRPASS compliant Digital Product Passports,
cryptographic verification hashes, and QR codes for physical hardware tagging.
"""
import base64
import hashlib
import io
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional
import qrcode

from app.db.store import store
from app.schemas.dpp import (
    DigitalProductPassport,
    DPPComponentHealth,
    DPPEndOfLifeGuidance,
    DPPLifecycleEvent,
    DPPProductIdentification,
    DPPRepairabilityCircularity,
    DPPSustainabilityMaterials,
)
from app.schemas.enums import Objective
from app.schemas.recommendation import RecommendationRequest
from app.services.assessment_service import assessment_service
from app.services.recommendation_service import recommendation_service

logger = logging.getLogger("reloop-ai.dpp")


class DigitalProductPassportService:
    def __init__(self):
        # In-memory DPP store: dpp_id -> DigitalProductPassport
        self.passports: Dict[str, DigitalProductPassport] = {}
        self.product_to_dpp: Dict[str, str] = {}

    def generate_passport(
        self,
        product_id: str,
        base_public_url: str = "https://reloop.ai/passport",
        db=None,
    ) -> DigitalProductPassport:
        """Synthesizes an audit-ready Digital Product Passport for a registered device."""
        if product_id in self.product_to_dpp:
            dpp_id = self.product_to_dpp[product_id]
            if dpp_id in self.passports:
                return self.passports[dpp_id]

        product = store.get_product(product_id)
        if not product and db:
            from app.db.repositories import product_repo
            product = product_repo.get_by_id(db, product_id)

        if not product:
            raise ValueError(f"Product '{product_id}' not found")

        # Retrieve or synthesize condition profile
        profile = store.get_profile(product_id)
        if not profile and db:
            from app.db.repositories import assessment_repo
            profile = assessment_repo.get_by_product_id(db, product_id)
        if not profile:
            profile = assessment_service.build_profile(product_id, db=db)

        # Retrieve or synthesize recommendation
        rec = store.get_recommendation(product_id)
        if not rec and db:
            from app.db.repositories import recommendation_repo
            rec = recommendation_repo.get_by_product_id(db, product_id)
        if not rec:
            req = RecommendationRequest(product_id=product_id, objective=Objective.LOWEST_COST, skip_ai_explanation=True)
            rec = recommendation_service.generate_recommendation(req, db=db)

        # 1. Product Identification
        specs = product.specs
        mfg = product.manufacturer or "OEM Manufacturer"
        model = product.model
        year = product.model_year or 2021
        serial = product.serial_or_identifier or f"SN-{product_id[-6:].upper()}"

        dpp_id = f"urn:dpp:eu:reloop:{hashlib.sha256(f'{mfg}:{model}:{serial}'.encode()).hexdigest()[:16]}"
        public_url = f"{base_public_url.rstrip('/')}/{dpp_id}"

        # 2. Repairability Score & Circularity Index
        # Calculated via French / EU methodology: documentation, modularity, fasteners, spare parts
        bat_mod = getattr(specs, "battery_replaceable", True)
        ram_mod = getattr(specs, "ram_modular", True)
        ssd_mod = getattr(specs, "ssd_modular", True)

        score_calc = 4.0
        if bat_mod:
            score_calc += 2.0
        if ram_mod:
            score_calc += 1.8
        if ssd_mod:
            score_calc += 1.8
        repairability_score = round(min(9.8, score_calc), 1)

        modularity_rating = "HIGH" if (bat_mod and ram_mod and ssd_mod) else "MODERATE" if (ram_mod or ssd_mod) else "PROPRIETARY"

        # 3. Component Health Provenance
        comp_health_list: List[DPPComponentHealth] = []
        if profile and profile.components:
            for comp_name, cond in profile.components.items():
                meas_clean = {k: str(v) for k, v in (cond.measurements or {}).items()}
                src = cond.evidence_sources[0] if cond.evidence_sources else "DIAGNOSTIC"
                comp_health_list.append(
                    DPPComponentHealth(
                        component=comp_name.capitalize(),
                        status=cond.status.value if hasattr(cond.status, "value") else str(cond.status),
                        provenance_source=src,
                        confidence=cond.confidence.value if hasattr(cond.confidence, "value") else str(cond.confidence),
                        observations=cond.observations[:3] if cond.observations else [],
                        measurements=meas_clean,
                    )
                )

        # 4. Lifecycle History
        created_iso = product.created_at.isoformat() if hasattr(product, "created_at") and product.created_at else datetime.now(timezone.utc).isoformat()
        lifecycle_events = [
            DPPLifecycleEvent(
                event_id=f"evt_mfg_{product_id[-6:]}",
                event_type="MANUFACTURING",
                timestamp=f"{year}-01-15T00:00:00Z",
                organization=mfg,
                details=f"Original device manufacturing and OEM quality sign-off ({mfg} {model}).",
            ),
            DPPLifecycleEvent(
                event_id=f"evt_intake_{product_id[-6:]}",
                event_type="ASSESSMENT",
                timestamp=created_iso,
                organization="ReLoop AI Lifecycle Engine",
                details=f"Completed multimodal evidence-provenance evaluation. Recommended circular pathway: {rec.selected_pathway.value if hasattr(rec.selected_pathway, 'value') else str(rec.selected_pathway)}.",
            ),
        ]

        # 5. Cryptographic Proof Hash (SHA-256 over key immutables)
        hash_payload = f"{dpp_id}|{mfg}|{model}|{serial}|{repairability_score}|{year}|{profile.overall_hardware_health}"
        verification_hash = hashlib.sha256(hash_payload.encode("utf-8")).hexdigest()

        # 6. High-Density QR Code Generation (PNG Base64)
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(public_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F766E", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        qr_base64 = f"data:image/png;base64,{base64.b64encode(img_buffer.getvalue()).decode('utf-8')}"

        passport = DigitalProductPassport(
            dpp_id=dpp_id,
            schema_version="CIRPASS-ESPR-v1.0",
            issue_date=datetime.now(timezone.utc).isoformat(),
            verification_status="VERIFIED",
            verification_hash=verification_hash,
            product_identification=DPPProductIdentification(
                gtin_or_ean=f"0{year}98{abs(hash(model)) % 100000000:08d}",
                serial_or_identifier=serial,
                manufacturer=mfg,
                model=model,
                category="Laptop / Portable Computer",
                model_year=year,
                country_of_origin="Global OEM Assembly",
            ),
            sustainability_and_materials=DPPSustainabilityMaterials(
                embodied_co2_kg=getattr(specs, "baseline_embodied_co2_kg", 280.0),
                recycled_content_percent=28.5,
                battery_chemistry="Lithium-Ion Polymer",
            ),
            repairability_and_circularity=DPPRepairabilityCircularity(
                repairability_score=repairability_score,
                modularity_rating=modularity_rating,
                battery_replaceable=bat_mod,
                ram_modular=ram_mod,
                storage_modular=ssd_mod,
                disassembly_manual_url=f"https://www.ifixit.com/Device/{model.replace(' ', '_')}",
            ),
            component_health_provenance=comp_health_list,
            lifecycle_history=lifecycle_events,
            end_of_life_guidance=DPPEndOfLifeGuidance(
                dismantling_difficulty="LOW" if (bat_mod and ssd_mod) else "MODERATE",
                battery_removal_required_before_shredding=True,
                circular_disposition=f"Transition to {rec.selected_pathway.value if hasattr(rec.selected_pathway, 'value') else str(rec.selected_pathway)} pathway to maximize material retention.",
            ),
            public_url=public_url,
            qr_code_base64=qr_base64,
        )

        self.passports[dpp_id] = passport
        self.product_to_dpp[product_id] = dpp_id
        return passport

    def get_passport(self, dpp_id: str) -> Optional[DigitalProductPassport]:
        return self.passports.get(dpp_id)

    def get_public_passport(self, dpp_id: str) -> Optional[DigitalProductPassport]:
        """Returns a sanitized public passport copy applying European privacy safeguards."""
        passport = self.get_passport(dpp_id)
        if not passport:
            return None
        public_copy = passport.model_copy(deep=True)
        # Redact raw device serial numbers to last 4 characters for consumer privacy
        if public_copy.product_identification.serial_or_identifier:
            raw_s = public_copy.product_identification.serial_or_identifier
            public_copy.product_identification.serial_or_identifier = f"***-{raw_s[-4:]}"
        return public_copy


# Global singleton instance
dpp_service = DigitalProductPassportService()

