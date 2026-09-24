"""
Product service managing device identification, specification lookup, and persistence.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from app.ai.gemini_client import gemini_client
from app.db.repositories import product_repo, evidence_repo
from app.db.store import store
from app.knowledge.models_catalog import lookup_model, get_all_models, CATALOG
from app.schemas.enums import ConfidenceLevel, DeviceCategory, EvidenceType
from app.schemas.errors import AppException, ErrorCode
from app.schemas.evidence import EvidenceItem
from app.schemas.product import (
    ProductCandidate,
    ProductCreate,
    ProductIdentificationRequest,
    ProductIdentificationResponse,
    ProductRecord,
    ProductSpecs,
)


class ProductService:
    def identify(self, req: ProductIdentificationRequest) -> ProductIdentificationResponse:
        hint = req.manual_model or ""
        if not hint and req.image_names:
            hint = " ".join(req.image_names)

        # 1. First try catalog lookup if manual model given
        matched_catalog = lookup_model(hint) if hint else None

        if matched_catalog:
            primary_candidate = ProductCandidate(
                manufacturer=matched_catalog["manufacturer"],
                model=matched_catalog["model"],
                model_year=matched_catalog["model_year"],
                confidence=ConfidenceLevel.HIGH,
                specs=matched_catalog["specs"],
            )
            clues = [
                f"Matched against hardware catalog for {matched_catalog['manufacturer']} {matched_catalog['model']}",
                f"Architecture profile: {'Modular' if matched_catalog['specs'].ram_modular else 'Soldered'} RAM, {'Modular' if matched_catalog['specs'].ssd_modular else 'Soldered'} SSD",
            ]
        else:
            # 2. Use Gemini vision / identification
            ai_res = gemini_client.identify_product(hint_text=hint)
            cat_match = lookup_model(ai_res.get("model", "")) or lookup_model(ai_res.get("manufacturer", ""))

            if cat_match:
                specs = cat_match["specs"]
                mfg = cat_match["manufacturer"]
                model = cat_match["model"]
                year = cat_match["model_year"]
            else:
                specs = ProductSpecs()
                mfg = ai_res.get("manufacturer", "Generic")
                model = ai_res.get("model", "Laptop")
                year = ai_res.get("model_year", 2020)

            primary_candidate = ProductCandidate(
                manufacturer=mfg,
                model=model,
                model_year=year,
                confidence=ConfidenceLevel.HIGH if cat_match else ConfidenceLevel.MEDIUM,
                specs=specs,
            )
            clues = ai_res.get("visual_clues", ["Visible chassis layout", "Brand aesthetic profile"])

        # Prepare alternative models from catalog
        all_candidates = get_all_models()
        alternatives = [
            c for c in all_candidates
            if not (c.manufacturer == primary_candidate.manufacturer and c.model == primary_candidate.model)
        ][:3]

        return ProductIdentificationResponse(
            identified_model=primary_candidate,
            alternative_models=alternatives,
            visual_clues=clues,
            requires_user_confirmation=True,
        )

    def create_or_confirm(self, data: ProductCreate, db: Optional[Session] = None) -> ProductRecord:
        catalog_match = lookup_model(f"{data.manufacturer} {data.model}")
        specs = catalog_match["specs"] if catalog_match else ProductSpecs()

        age = data.age_years
        if age is None:
            age = max(1.0, float(2026 - data.model_year))

        product = ProductRecord(
            manufacturer=data.manufacturer,
            model=data.model,
            model_year=data.model_year,
            category=data.category,
            serial_or_identifier=data.serial_or_identifier,
            age_years=age,
            specs=specs,
        )

        if db:
            saved = product_repo.create(db, product)
            # Record database evidence of model specs
            spec_ev = EvidenceItem(
                type=EvidenceType.DATABASE,
                source=f"Hardware Specification Catalog ({saved.manufacturer} {saved.model})",
                component="system",
                value={
                    "ram_modular": specs.ram_modular,
                    "ssd_modular": specs.ssd_modular,
                    "battery_replaceable": specs.battery_replaceable,
                    "baseline_embodied_co2_kg": specs.baseline_embodied_co2_kg,
                    "model_year": saved.model_year,
                },
                confidence=ConfidenceLevel.HIGH,
            )
            evidence_repo.add(db, spec_ev, product_id=saved.id)
            store.save_product(saved)
            store.add_evidence(saved.id, spec_ev)
            return saved

        saved = store.save_product(product)
        # Record database evidence of model specs
        store.add_evidence(
            saved.id,
            EvidenceItem(
                type=EvidenceType.DATABASE,
                source=f"Hardware Specification Catalog ({saved.manufacturer} {saved.model})",
                component="system",
                value={
                    "ram_modular": specs.ram_modular,
                    "ssd_modular": specs.ssd_modular,
                    "battery_replaceable": specs.battery_replaceable,
                    "baseline_embodied_co2_kg": specs.baseline_embodied_co2_kg,
                    "model_year": saved.model_year,
                },
                confidence=ConfidenceLevel.HIGH,
            ),
        )
        return saved

    def get_by_id(self, product_id: str, db: Optional[Session] = None) -> ProductRecord:
        prod = None
        if db:
            prod = product_repo.get_by_id(db, product_id)
        if not prod:
            prod = store.get_product(product_id)

        if not prod:
            raise AppException(
                code=ErrorCode.NOT_FOUND.value,
                message=f"No product found with id '{product_id}'",
                field="product_id",
                http_status=404,
            )
        return prod


product_service = ProductService()
