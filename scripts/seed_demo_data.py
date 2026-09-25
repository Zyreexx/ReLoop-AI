#!/usr/bin/env python3
"""
Seed script to load structured demo cases into PostgreSQL database.
Idempotent: Safely wipes and re-loads demo product data only.

Usage:
    python scripts/seed_demo_data.py
    (or from backend/: python ../scripts/seed_demo_data.py)
"""
import json
import logging
import os
import sys
from pathlib import Path

# Ensure backend directory is in sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
BACKEND_DIR = REPO_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_demo_data")

from app.db.base import Base
from app.db.session import SessionLocal, create_all_tables, engine
from app.db.repositories import (
    assessment_repo,
    evidence_repo,
    product_repo,
    recommendation_repo,
)
from app.knowledge import get_demo_data_dir, get_model_spec
from app.models.entities import (
    Assessment as AssessmentModel,
    ComponentConditionRecord as ComponentConditionModel,
    Evidence as EvidenceModel,
    Product as ProductModel,
    RecommendationRecord as RecommendationModel,
)
from app.optimizer.scorer import score_pathways
from app.schemas.condition import AssessmentBuildResponse, ComponentCondition, ConditionProfile
from app.schemas.enums import (
    ComponentName,
    ComponentStatus,
    ConfidenceLevel,
    DeviceCategory,
    EvidenceType,
    Objective,
    PathwayType,
)
from app.schemas.evidence import Evidence, EvidenceItem
from app.schemas.product import Product, ProductSpecs


DEMO_PRODUCT_IDS = {
    "demo-01-healthy": "prod_demo_01_healthy",
    "demo-02-repairable": "prod_demo_02_repairable",
    "demo-03-borderline": "prod_demo_03_borderline",
    "demo-04-recovery": "prod_demo_04_recovery",
}


def wipe_demo_data(db) -> None:
    """
    Wipes existing demo products and associated records to guarantee idempotency.
    Only touches product records prefixed with demo IDs.
    """
    demo_ids = list(DEMO_PRODUCT_IDS.values())
    logger.info(f"Cleaning existing demo records for IDs: {demo_ids}...")

    # Delete existing recommendations
    db.query(RecommendationModel).filter(RecommendationModel.product_id.in_(demo_ids)).delete(synchronize_session=False)

    # Delete existing assessments and component conditions
    existing_assessments = db.query(AssessmentModel).filter(AssessmentModel.product_id.in_(demo_ids)).all()
    for ass in existing_assessments:
        db.query(ComponentConditionModel).filter(ComponentConditionModel.assessment_id == ass.id).delete(synchronize_session=False)
        db.delete(ass)

    # Delete existing evidence
    db.query(EvidenceModel).filter(EvidenceModel.product_id.in_(demo_ids)).delete(synchronize_session=False)

    # Delete existing products
    db.query(ProductModel).filter(ProductModel.id.in_(demo_ids)).delete(synchronize_session=False)

    db.commit()
    logger.info("Previous demo data wiped successfully.")


def load_demo_cases() -> list:
    demo_dir = get_demo_data_dir()
    if not demo_dir.exists():
        logger.error(f"Demo directory not found at {demo_dir}")
        return []

    cases = []
    for f in sorted(demo_dir.glob("*.json")):
        with open(f, "r", encoding="utf-8") as json_file:
            cases.append(json.load(json_file))
    return cases


def seed_demo_case(db, demo_data: dict) -> None:
    demo_id = demo_data["id"]
    prod_id = DEMO_PRODUCT_IDS.get(demo_id, f"prod_{demo_id.replace('-', '_')}")
    prod_info = demo_data["product"]

    logger.info(f"Seeding demo case '{demo_id}' -> Product ID '{prod_id}' ({prod_info['manufacturer']} {prod_info['model']})...")

    # 1. Look up specs from knowledge catalog
    try:
        model_spec = get_model_spec(f"{prod_info['manufacturer']} {prod_info['model']}")
        specs_data = model_spec.get("specs", {})
        specs = ProductSpecs(**specs_data)
    except Exception:
        specs_data = prod_info.get("specs", {})
        specs = ProductSpecs(**specs_data)

    product = Product(
        id=prod_id,
        manufacturer=prod_info["manufacturer"],
        model=prod_info["model"],
        model_year=prod_info.get("model_year", 2020),
        category=DeviceCategory.LAPTOP,
        age=float(prod_info.get("age_years", 3.0)),
        specs=specs,
    )
    saved_product = product_repo.create(db, product)

    # 2. Add Baseline Database Evidence
    ev_spec = Evidence(
        product_id=prod_id,
        type=EvidenceType.DATABASE,
        source=f"Hardware Specification Catalog ({product.manufacturer} {product.model})",
        component="system",
        value={
            "ram_modular": specs.ram_modular,
            "ssd_modular": specs.ssd_modular,
            "battery_replaceable": specs.battery_replaceable,
            "baseline_embodied_co2_kg": specs.baseline_embodied_co2_kg,
            "model_year": product.model_year,
            "basis": "assumption",
            "note": "Curated hardware knowledge base baseline specifications.",
        },
        confidence=ConfidenceLevel.HIGH,
    )
    evidence_repo.add(db, ev_spec)

    # 3. Add Vision Findings Evidence
    vision_findings = demo_data.get("vision_findings", {})
    for dmg in vision_findings.get("visible_damages", []):
        ev_vis = Evidence(
            product_id=prod_id,
            type=EvidenceType.VISUAL,
            source="Computer Vision Inspection (Simulated Multimodal AI)",
            component=dmg.get("component", "chassis"),
            value={
                "description": dmg.get("description"),
                "severity": dmg.get("severity", "LOW"),
                "cosmetic_grade": vision_findings.get("cosmetic_grade", "B"),
                "basis": "assumption",
                "note": "Simulated visual inspection finding.",
            },
            confidence=ConfidenceLevel.HIGH,
        )
        evidence_repo.add(db, ev_vis)

    # 4. Add Diagnostic Evidence
    diagnostics = demo_data.get("diagnostics", {})
    for comp_name, diag_data in diagnostics.items():
        if comp_name in ["basis", "note"]:
            continue
        ev_diag = Evidence(
            product_id=prod_id,
            type=EvidenceType.DIAGNOSTIC,
            source=f"Hardware Diagnostic Engine ({comp_name.upper()})",
            component=comp_name,
            value={
                **diag_data,
                "basis": "assumption",
                "note": "Standardized component diagnostic measurement.",
            },
            confidence=ConfidenceLevel.HIGH,
        )
        evidence_repo.add(db, ev_diag)

    # 5. Add User Reported Symptoms Evidence
    user_symptoms = demo_data.get("user_symptoms", {})
    ev_user = Evidence(
        product_id=prod_id,
        type=EvidenceType.USER_REPORTED,
        source="Customer Intake Survey",
        component="system",
        value={
            "reported_issues": user_symptoms.get("reported_issues", []),
            "target_objective": user_symptoms.get("target_objective", "MAX_LIFE"),
            "daily_usage_hours": user_symptoms.get("daily_usage_hours", 6.0),
            "basis": "assumption",
            "note": "User-reported intake symptoms.",
        },
        confidence=ConfidenceLevel.MEDIUM,
    )
    evidence_repo.add(db, ev_user)

    # 6. Build Component Conditions
    components_map = {}
    for comp_name, diag_val in diagnostics.items():
        if comp_name in ["basis", "note"] or not isinstance(diag_val, dict):
            continue
        status_str = diag_val.get("status", "GOOD").upper()
        if status_str in ["GOOD", "PASS"]:
            status = ComponentStatus.GOOD
        elif status_str in ["WEAR", "FAIR", "SERVICE_REQUIRED"]:
            status = ComponentStatus.WEAR
        elif status_str in ["REPLACE", "FAIL", "REPLACE_REQUIRED"]:
            status = ComponentStatus.REPLACE
        elif status_str in ["DAMAGED"]:
            status = ComponentStatus.DAMAGED
        else:
            status = ComponentStatus.UNKNOWN

        cond = ComponentCondition(
            component=ComponentName(comp_name.upper()) if comp_name.upper() in ComponentName._value2member_map_ else comp_name,
            status=status,
            observations=[diag_val.get("note", f"{comp_name} diagnostic evaluated")],
            measurements=diag_val,
            confidence=ConfidenceLevel.HIGH,
            label=f"{comp_name.capitalize()} Condition",
            repairable=(status in [ComponentStatus.WEAR, ComponentStatus.REPLACE] and comp_name != "system"),
            upgradeable=(comp_name in ["ssd", "ram"] and getattr(specs, f"{comp_name}_modular", True)),
        )
        components_map[comp_name] = cond

    # Fill default components if missing
    for c_key in ["battery", "ssd", "ram", "thermals", "display", "keyboard", "chassis", "system"]:
        if c_key not in components_map:
            components_map[c_key] = ComponentCondition(
                component=ComponentName(c_key.upper()) if c_key.upper() in ComponentName._value2member_map_ else c_key,
                status=ComponentStatus.GOOD,
                observations=["No faults detected"],
                measurements={},
                confidence=ConfidenceLevel.HIGH,
            )

    # 7. Persist Assessment
    all_ev = evidence_repo.get_by_product_id(db, prod_id)
    health_str_map = {
        "demo-01-healthy": "GOOD",
        "demo-02-repairable": "FAIR",
        "demo-03-borderline": "DEGRADED",
        "demo-04-recovery": "CRITICAL",
    }
    assessment = AssessmentBuildResponse(
        product_id=prod_id,
        overall_hardware_health=health_str_map.get(demo_id, "FAIR"),
        components=components_map,
        all_evidence=all_ev,
    )
    assessment_repo.save(db, assessment)

    # 8. Deterministic Optimizer Scoring & Recommendation Save
    obj_str = user_symptoms.get("target_objective", "MAX_LIFE").upper()
    try:
        target_obj = Objective(obj_str)
    except Exception:
        target_obj = Objective.MAX_LIFE

    profile = ConditionProfile(
        product_id=prod_id,
        components=components_map,
    )
    rec = score_pathways(saved_product, profile, target_obj)
    recommendation_repo.save(db, rec)
    logger.info(f"Successfully seeded '{demo_id}' -> Pathway: {rec.selected_pathway.value}, Score: {rec.score:.1f}")


def main() -> None:
    logger.info("Initializing database tables...")
    create_all_tables()

    db = SessionLocal()
    try:
        wipe_demo_data(db)
        demo_cases = load_demo_cases()
        logger.info(f"Loaded {len(demo_cases)} demo cases from data/demo/.")
        for case in demo_cases:
            seed_demo_case(db, case)
        logger.info("Database demo seed completed successfully!")
    except Exception as e:
        db.rollback()
        logger.error(f"Error seeding demo data: {e}", exc_info=True)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
