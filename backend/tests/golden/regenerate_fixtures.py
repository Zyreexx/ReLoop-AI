"""
Utility script to regenerate golden test fixtures for the circular optimizer.
Reads data/demo/*.json, scores all 4 demo cases across all 4 objectives,
and updates the golden fixtures in backend/tests/golden/.

Usage:
    python backend/tests/golden/regenerate_fixtures.py
"""
import json
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(backend_dir))

from app.knowledge import get_demo_data_dir
from app.optimizer.scorer import score_pathways
from app.schemas.condition import ComponentCondition, ConditionProfile
from app.schemas.enums import ComponentStatus, DeviceCategory, Objective
from app.schemas.product import ProductRecord, ProductSpecs

GOLDEN_DIR = Path(__file__).resolve().parent


def parse_demo_case(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as jf:
        data = json.load(jf)

    p_data = data["product"]
    specs_data = p_data.get("specs", {})
    specs = ProductSpecs(
        category=DeviceCategory.LAPTOP,
        ram_modular=specs_data.get("ram_modular", True),
        ssd_modular=specs_data.get("ssd_modular", True),
        battery_replaceable=specs_data.get("battery_replaceable", True),
        weight_kg=specs_data.get("weight_kg", 1.4),
        baseline_embodied_co2_kg=specs_data.get("baseline_embodied_co2_kg", 300.0),
        estimated_original_msrp_usd=specs_data.get("estimated_original_msrp_usd", 1200.0),
    )
    product = ProductRecord(
        id=data["id"],
        manufacturer=p_data["manufacturer"],
        model=p_data["model"],
        model_year=p_data["model_year"],
        category=DeviceCategory.LAPTOP,
        age_years=p_data.get("age_years", 3.0),
        specs=specs,
    )

    components = {}
    for comp_name, comp_diag in data.get("diagnostics", {}).items():
        if comp_name in ["basis", "note"]:
            continue
        status_raw = comp_diag.get("status", "GOOD")
        repairable = status_raw in ["WEAR", "SERVICE_REQUIRED", "REPLACE", "REPLACE_REQUIRED", "DAMAGED"]
        upgradeable = comp_name in ["ssd", "ram"]
        components[comp_name] = ComponentCondition(
            component=comp_name,
            status=(
                ComponentStatus(status_raw)
                if status_raw in ComponentStatus._value2member_map_
                else ComponentStatus.GOOD
            ),
            label=f"{comp_name.title()} ({status_raw})",
            repairable=repairable,
            upgradeable=upgradeable,
        )
    for vis in data.get("vision_findings", {}).get("visible_damages", []):
        c_name = vis.get("component", "chassis")
        if c_name not in components:
            components[c_name] = ComponentCondition(
                component=c_name,
                status=ComponentStatus.GOOD if vis.get("severity") == "NONE" else ComponentStatus.WEAR,
                label=vis.get("description", ""),
                repairable=vis.get("severity") not in ["NONE", "LOW"],
            )

    profile = ConditionProfile(product_id=product.id, components=components)
    return product, profile, data


def regenerate():
    demo_dir = get_demo_data_dir()
    demo_files = sorted(demo_dir.glob("*.json"))

    if not demo_files:
        print(f"Error: No demo files found in {demo_dir}")
        sys.exit(1)

    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)

    objectives = [
        Objective.LOWEST_COST,
        Objective.MAX_LIFE,
        Objective.ENVIRONMENTAL,
        Objective.FASTEST_RECOVERY,
    ]

    for demo_file in demo_files:
        product, profile, raw_data = parse_demo_case(demo_file)
        case_id = raw_data["id"]
        golden_payload = {
            "case_id": case_id,
            "demo_file": demo_file.name,
            "title": raw_data["title"],
            "product": {
                "manufacturer": product.manufacturer,
                "model": product.model,
                "model_year": product.model_year,
            },
            "objectives": {},
        }

        for obj in objectives:
            rec = score_pathways(product, profile, obj)
            ranking = [rec.primary_recommendation.pathway.type.value] + [
                alt.pathway.type.value for alt in rec.alternative_pathways
            ]
            scores = [rec.primary_recommendation.score] + [
                alt.score for alt in rec.alternative_pathways
            ]
            scored_ranking = [
                {"rank": i + 1, "pathway": p, "score": s}
                for i, (p, s) in enumerate(zip(ranking, scores))
            ]

            golden_payload["objectives"][obj.value] = {
                "selected_pathway": rec.selected_pathway.value,
                "primary_score": rec.score,
                "ranked_pathways": ranking,
                "scored_ranking": scored_ranking,
            }

        target_file = GOLDEN_DIR / f"{demo_file.stem}.json"
        with open(target_file, "w", encoding="utf-8") as out:
            json.dump(golden_payload, out, indent=2)

        print(f"Wrote golden fixture: {target_file.name}")


if __name__ == "__main__":
    regenerate()
