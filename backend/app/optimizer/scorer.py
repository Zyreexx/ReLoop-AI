"""
Deterministic scoring engine for circular pathways.
Zero AI imports — 100% deterministic Python calculation.
"""
from typing import Dict, List, Tuple
from app.schemas.enums import ObjectiveType, PathwayType, ComponentStatus
from app.schemas.condition import ConditionProfile
from app.schemas.product import ProductRecord
from app.schemas.pathway import PathwayOption
from app.schemas.recommendation import (
    ScoredPathway,
    RecommendationResponse,
    SecondLifeSuggestion,
    ComponentRecoveryManifest,
)
from app.optimizer.pathways import generate_all_pathways


OBJECTIVE_WEIGHTS: Dict[ObjectiveType, Dict[str, float]] = {
    ObjectiveType.MAXIMUM_LIFE: {
        "w_life": 0.35,
        "w_value": 0.20,
        "w_material": 0.15,
        "w_env": 0.15,
        "w_cost": 0.10,
        "w_logistics": 0.05,
    },
    ObjectiveType.LOWEST_COST: {
        "w_cost": 0.40,
        "w_life": 0.20,
        "w_value": 0.15,
        "w_logistics": 0.10,
        "w_material": 0.08,
        "w_env": 0.07,
    },
    ObjectiveType.ENVIRONMENTAL_BENEFIT: {
        "w_env": 0.35,
        "w_material": 0.25,
        "w_life": 0.20,
        "w_value": 0.10,
        "w_cost": 0.05,
        "w_logistics": 0.05,
    },
    ObjectiveType.FASTEST_RECOVERY: {
        "w_logistics": 0.35,
        "w_value": 0.25,
        "w_life": 0.15,
        "w_cost": 0.15,
        "w_material": 0.05,
        "w_env": 0.05,
    },
}


def score_pathways(
    product: ProductRecord,
    profile: ConditionProfile,
    objective: ObjectiveType = ObjectiveType.MAXIMUM_LIFE,
) -> RecommendationResponse:
    pathways = generate_all_pathways(product, profile)
    weights = OBJECTIVE_WEIGHTS.get(objective, OBJECTIVE_WEIGHTS[ObjectiveType.MAXIMUM_LIFE])

    scored: List[ScoredPathway] = []

    for p in pathways:
        # Life extension (0 to 5 years normalized)
        avg_life = (p.expected_life_extension_years.min_val + p.expected_life_extension_years.max_val) / 2.0
        norm_life = min(1.0, max(0.0, avg_life / 5.0))

        # Value retained (0 to 100%)
        norm_value = min(1.0, max(0.0, p.value_retained_percentage / 100.0))

        # Material retained (0 to 100%)
        norm_material = min(1.0, max(0.0, p.material_retained_percentage / 100.0))

        # Environmental benefit (CO2 avoided 0 to 300kg)
        avg_co2 = (p.environmental_estimate.co2_avoided_kg_min + p.environmental_estimate.co2_avoided_kg_max) / 2.0
        norm_env = min(1.0, max(0.0, avg_co2 / 300.0))

        # Cost penalty (0 to $300)
        avg_cost = (p.estimated_cost.min_val + p.estimated_cost.max_val) / 2.0
        norm_cost = min(1.0, max(0.0, avg_cost / 300.0))

        # Logistics penalty (turnaround 0 to 10 days)
        avg_days = (p.logistics.turnaround_days_min + p.logistics.turnaround_days_max) / 2.0
        norm_logistics = min(1.0, max(0.0, avg_days / 10.0))

        subscores = {
            "life_extension": round(norm_life, 3),
            "value_retained": round(norm_value, 3),
            "material_retained": round(norm_material, 3),
            "environmental_benefit": round(norm_env, 3),
            "cost_economy": round(1.0 - norm_cost, 3),
            "logistics_speed": round(1.0 - norm_logistics, 3),
        }

        # Formula from docs/architecture.md and rules.md
        raw_score = (
            weights["w_life"] * norm_life
            + weights["w_value"] * norm_value
            + weights["w_material"] * norm_material
            + weights["w_env"] * norm_env
            + weights["w_cost"] * (1.0 - norm_cost)
            + weights["w_logistics"] * (1.0 - norm_logistics)
        )

        final_score = round(raw_score * 100.0, 1)

        # Ineligible pathways receive heavy penalty to ensure they rank below eligible ones
        if not p.eligibility.is_eligible:
            final_score = round(final_score * 0.15, 1)

        scored.append(
            ScoredPathway(
                pathway=p,
                score=final_score,
                rank=0,
                normalized_subscores=subscores,
            )
        )

    # Sort descending by score, prioritizing eligible over ineligible
    scored.sort(
        key=lambda item: (item.pathway.eligibility.is_eligible, item.score),
        reverse=True,
    )

    for i, item in enumerate(scored):
        item.rank = i + 1

    primary = scored[0]
    alternatives = scored[1:]

    # Build reasoning bullets based on verified evidence
    reasoning, evidence_ids = derive_reasoning(primary.pathway, profile, objective)

    # Second life suggestion if appropriate
    second_life = None
    if primary.pathway.type in [PathwayType.REUSE_REDEPLOY, PathwayType.REPAIR, PathwayType.UPGRADE]:
        second_life = SecondLifeSuggestion(
            suggested_role="Digital Education / Linux Workstation / Light Office",
            target_user="Secondary student, vocational trainee, or remote administrative worker",
            os_recommendation="Ubuntu 24.04 LTS or ChromeOS Flex",
            workloads=[
                "Web browsing & document processing",
                "Python and web programming learning",
                "Video conferencing & remote learning",
            ],
            basis="SPEC_MATCHING_HEURISTIC",
        )

    # Component recovery manifest if selected or as salvage option
    recovery_manifest = None
    if primary.pathway.type == PathwayType.COMPONENT_RECOVERY or not primary.pathway.eligibility.is_eligible:
        salvageable_parts = []
        val_est = 0.0
        ssd = profile.get_component("ssd")
        if ssd and ssd.status in [ComponentStatus.GOOD, ComponentStatus.FAIR] and product.specs.ssd_modular:
            salvageable_parts.append(f"M.2 NVMe SSD ({ssd.label})")
            val_est += 35.0
        ram = profile.get_component("ram")
        if ram and ram.status == ComponentStatus.GOOD and product.specs.ram_modular:
            salvageable_parts.append(f"SO-DIMM RAM Module ({ram.label})")
            val_est += 25.0
        disp = profile.get_component("display")
        if disp and disp.status == ComponentStatus.GOOD:
            salvageable_parts.append("Display Panel Assembly")
            val_est += 50.0

        recovery_manifest = ComponentRecoveryManifest(
            recoverable_parts=salvageable_parts,
            salvage_value_estimate_usd=val_est,
            material_recovery_action="Harvest intact subcomponents into spare parts inventory; route residual inert shell to certified WEEE smelter.",
        )

    return RecommendationResponse(
        product_id=product.id,
        objective=objective,
        selected_pathway=primary.pathway.type,
        primary_recommendation=primary,
        alternative_pathways=alternatives,
        reasoning=reasoning,
        linked_evidence_ids=evidence_ids,
        explicit_assumptions=primary.pathway.assumptions + [
            f"Optimized for {objective.value.replace('_', ' ').title()}",
            "Deterministic scoring normalized across durability, retained value, material loop, and cost parameters",
        ],
        second_life=second_life,
        component_recovery=recovery_manifest,
    )


def derive_reasoning(
    pathway: PathwayOption, profile: ConditionProfile, objective: ObjectiveType
) -> Tuple[List[str], List[str]]:
    bullets: List[str] = []
    linked_ids: List[str] = []

    battery = profile.get_component("battery")
    ssd = profile.get_component("ssd")
    ram = profile.get_component("ram")
    thermals = profile.get_component("thermals")
    system = profile.get_component("system")
    display = profile.get_component("display")

    if pathway.type == PathwayType.REPAIR:
        if battery and battery.status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.FAIR]:
            bullets.append(f"Battery health is at {battery.label}; targeted replacement restores mobile runtime.")
            linked_ids.extend(battery.evidence_ids)
        if thermals and thermals.status != ComponentStatus.GOOD:
            bullets.append(f"Thermals indicate {thermals.label}; repasting avoids aggressive CPU throttling.")
            linked_ids.extend(thermals.evidence_ids)
        if ssd and ssd.status == ComponentStatus.GOOD:
            bullets.append(f"Primary storage remains healthy ({ssd.label}); preserving drive saves both cost and manufacturing footprint.")
            linked_ids.extend(ssd.evidence_ids)
        if ram and ram.status == ComponentStatus.GOOD:
            bullets.append(f"RAM diagnostics show {ram.label}; core memory is stable.")
            linked_ids.extend(ram.evidence_ids)

    elif pathway.type == PathwayType.UPGRADE:
        bullets.append("Modular hardware architecture allows performance expansion without whole-device replacement.")
        if ram and ram.upgradeable:
            bullets.append("Memory capacity can be expanded via accessible SO-DIMM slots.")
        if ssd and ssd.upgradeable:
            bullets.append("Storage can be accelerated with modern high-speed NVMe.")

    elif pathway.type == PathwayType.REUSE_REDEPLOY:
        bullets.append("Core compute architecture is stable with zero critical logic faults.")
        bullets.append("Immediate redeployment avoids 100% of embodied product carbon emissions.")

    elif pathway.type == PathwayType.COMPONENT_RECOVERY:
        bullets.append("System chassis or board damage prevents economic whole-product service.")
        bullets.append("Salvageable modular components retain significant secondary utility in spare inventory.")

    elif pathway.type == PathwayType.REFURBISH:
        bullets.append("Comprehensive multi-point service restores commercial Grade A/B reliability for resale or redeployment.")

    elif pathway.type == PathwayType.RECYCLE:
        bullets.append("Higher circular loops are exhausted or non-viable; responsible material recycling reclaims copper, aluminum, and precious metals.")

    if not bullets:
        bullets.append(f"Pathway ranked highest under the {objective.value.replace('_', ' ').lower()} objective function.")

    return bullets, list(set(linked_ids))
