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
        from app.services.vision import vision_service
        return vision_service.identify(
            manual_model=req.manual_model,
            model_id=req.model_id,
            hint=req.hint or (" ".join(req.image_names) if req.image_names else None),
        )

    def create_or_confirm(self, data: ProductCreate, db: Optional[Session] = None) -> ProductRecord:
        from app.knowledge.loader import match_catalog_model, get_generic_laptop_profile
        catalog_match = match_catalog_model(data.manufacturer, data.model)
        if catalog_match:
            specs_data = catalog_match.get("specs", {})
            specs = ProductSpecs(**specs_data) if isinstance(specs_data, dict) else specs_data
            is_generic = False
        else:
            generic_prof = get_generic_laptop_profile()
            specs_data = generic_prof.get("specs", {})
            specs = ProductSpecs(**specs_data) if isinstance(specs_data, dict) else specs_data
            is_generic = True

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
            is_generic=is_generic,
            is_generic_assessment=is_generic,
        )

        source_label = (
            f"Hardware Specification Catalog ({product.manufacturer} {product.model})"
            if not is_generic
            else f"Generic Category Estimate ({product.manufacturer} {product.model})"
        )
        basis_val = "DATABASE" if not is_generic else "GENERIC_CATEGORY_ESTIMATE"
        conf_val = ConfidenceLevel.HIGH if not is_generic else ConfidenceLevel.MEDIUM

        if db:
            saved = product_repo.create(db, product)
            # Record database evidence of model specs
            spec_ev = EvidenceItem(
                type=EvidenceType.DATABASE,
                source=source_label,
                component="system",
                value={
                    "ram_modular": specs.ram_modular,
                    "ssd_modular": specs.ssd_modular,
                    "battery_replaceable": specs.battery_replaceable,
                    "baseline_embodied_co2_kg": specs.baseline_embodied_co2_kg,
                    "model_year": saved.model_year,
                    "basis": basis_val,
                },
                confidence=conf_val,
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
                source=source_label,
                component="system",
                value={
                    "ram_modular": specs.ram_modular,
                    "ssd_modular": specs.ssd_modular,
                    "battery_replaceable": specs.battery_replaceable,
                    "baseline_embodied_co2_kg": specs.baseline_embodied_co2_kg,
                    "model_year": saved.model_year,
                    "basis": basis_val,
                },
                confidence=conf_val,
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
