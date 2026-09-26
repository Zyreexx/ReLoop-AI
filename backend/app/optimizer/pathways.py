"""
Pathway metrics calculation and generation.
Pure deterministic logic without external AI calls.
"""
from typing import List, Dict
from app.schemas.enums import PathwayType, ComponentStatus
from app.schemas.condition import ConditionProfile
from app.schemas.product import ProductRecord, ProductSpecs
from app.schemas.pathway import (
    PathwayOption,
    RangeEstimate,
    EnvironmentalEstimate,
    LogisticsEstimate,
)
from app.optimizer.rules import (
    evaluate_repair_eligibility,
    evaluate_upgrade_eligibility,
    evaluate_refurbish_eligibility,
    evaluate_reuse_redeploy_eligibility,
    evaluate_component_recovery_eligibility,
    evaluate_recycle_eligibility,
)


def generate_all_pathways(
    product: ProductRecord, profile: ConditionProfile
) -> List[PathwayOption]:
    specs = product.specs
    pathways: List[PathwayOption] = []

    # 1. REPAIR
    repair_eligibility = evaluate_repair_eligibility(profile, specs)
    actions_repair = []
    cost_min, cost_max = 0.0, 0.0

    battery_cond = profile.get_component("battery")
    if battery_cond and battery_cond.status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.REPLACE_REQUIRED, ComponentStatus.FAIR]:
        actions_repair.append("Install certified replacement battery pack")
        cost_min += 45.0
        cost_max += 75.0

    keyboard_cond = profile.get_component("keyboard")
    if keyboard_cond and keyboard_cond.status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.REPLACE_REQUIRED]:
        actions_repair.append("Replace damaged keyboard module")
        cost_min += 30.0
        cost_max += 55.0

    thermals_cond = profile.get_component("thermals")
    if thermals_cond and thermals_cond.status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.FAIR]:
        actions_repair.append("Thermal service: heatsink dust clearing & high-performance thermal paste application")
        cost_min += 15.0
        cost_max += 30.0

    display_cond = profile.get_component("display")
    if display_cond and display_cond.status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.REPLACE_REQUIRED]:
        actions_repair.append("Replace damaged display panel")
        cost_min += 85.0
        cost_max += 140.0

    if cost_min == 0.0:
        cost_min, cost_max = 25.0, 50.0
        actions_repair.append("Preventative hardware tune-up")

    repair_pathway = PathwayOption(
        type=PathwayType.REPAIR,
        title="Targeted Component Repair",
        summary="Remedy specific degraded or damaged components to restore original operation.",
        eligibility=repair_eligibility,
        actions_required=actions_repair,
        estimated_cost=RangeEstimate(
            min_val=cost_min,
            max_val=cost_max,
            unit="INR",
            display_range=f"${int(cost_min)}–${int(cost_max)}",
            basis="DATABASE_ESTIMATE",
            assumptions=[
                "Standard OEM-compatible replacement parts readily available",
                "Work performed by independent repair technician or self-repair toolkit",
                "Internal logic board has no latent critical defects",
            ],
        ),
        expected_life_extension_years=RangeEstimate(
            min_val=2.5,
            max_val=4.5,
            unit="years",
            display_range="+2.5–4.5 years",
            basis="MODEL_ESTIMATE",
            assumptions=[
                "Thermal operating envelope restored below 80°C under load",
                "New battery cycled under standard consumer charging practices",
            ],
        ),
        value_retained_percentage=92.0,
        material_retained_percentage=96.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=210.0,
            co2_avoided_kg_max=275.0,
            ewaste_diverted_kg=round(specs.weight_kg * 0.96, 2),
            basis="LIFECYCLE_EMISSION_BENCHMARK",
            assumptions=[
                f"Defers full replacement of {specs.category.value.lower()} ({specs.baseline_embodied_co2_kg} kg baseline CO2e)",
                "Displaced emissions account for new battery manufacturing footprint (~12 kg CO2e)",
            ],
        ),
        logistics=LogisticsEstimate(
            complexity="LOW" if cost_max < 90 else "MODERATE",
            turnaround_days_min=1,
            turnaround_days_max=4,
            basis="SERVICE_BENCHMARK",
            assumptions=["Parts in regional distribution stock"],
        ),
        assumptions=[
            "Direct targeted repairs preserve 100% of user data and existing software configuration",
        ],
    )
    pathways.append(repair_pathway)

    # 2. UPGRADE
    upgrade_eligibility = evaluate_upgrade_eligibility(profile, specs)
    actions_upgrade = []
    up_cost_min, up_cost_max = 0.0, 0.0

    if specs.ram_modular:
        actions_upgrade.append("Expand RAM to 16GB/32GB DDR4/DDR5 SO-DIMM")
        up_cost_min += 35.0
        up_cost_max += 60.0
    if specs.ssd_modular:
        actions_upgrade.append("Upgrade NVMe SSD to fast 1TB Gen3/Gen4 drive")
        up_cost_min += 60.0
        up_cost_max += 95.0

    if not actions_upgrade:
        up_cost_min, up_cost_max = 0.0, 0.0
        actions_upgrade.append("Hardware architecture is fully soldered; upgrade unavailable")

    has_unaddressed_faults = any(
        profile.get_component(c) and profile.get_component(c).status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.REPLACE_REQUIRED]
        for c in ["battery", "thermals", "display"]
    )
    if has_unaddressed_faults:
        up_life_min, up_life_max = 1.0, 2.0
        up_life_display = "+1–2 years (constrained by unserviced components)"
        up_life_assumptions = ["Hardware responsiveness improved, but longevity remains constrained by unserviced thermal or battery degradation"]
    else:
        up_life_min, up_life_max = 2.5, 4.0
        up_life_display = "+2.5–4 years"
        up_life_assumptions = ["Base hardware is healthy; upgraded storage and RAM allow device to run modern software workloads comfortably"]

    upgrade_pathway = PathwayOption(
        type=PathwayType.UPGRADE,
        title="Hardware Performance Upgrade",
        summary="Boost responsiveness, multitasking headroom, and storage bandwidth with modern modular components.",
        eligibility=upgrade_eligibility,
        actions_required=actions_upgrade,
        estimated_cost=RangeEstimate(
            min_val=up_cost_min,
            max_val=up_cost_max,
            unit="INR",
            display_range=f"${int(up_cost_min)}–${int(up_cost_max)}" if up_cost_max > 0 else "N/A",
            basis="DATABASE_ESTIMATE",
            assumptions=[
                "Current market prices for standard consumer SO-DIMM and PCIe NVMe storage",
            ],
        ),
        expected_life_extension_years=RangeEstimate(
            min_val=up_life_min if upgrade_eligibility.is_eligible else 0.0,
            max_val=up_life_max if upgrade_eligibility.is_eligible else 0.0,
            unit="years",
            display_range=up_life_display if upgrade_eligibility.is_eligible else "+0 years",
            basis="MODEL_ESTIMATE",
            assumptions=up_life_assumptions,
        ),
        value_retained_percentage=85.0 if upgrade_eligibility.is_eligible else 40.0,
        material_retained_percentage=94.0 if upgrade_eligibility.is_eligible else 50.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=180.0 if upgrade_eligibility.is_eligible else 0.0,
            co2_avoided_kg_max=240.0 if upgrade_eligibility.is_eligible else 0.0,
            ewaste_diverted_kg=round(specs.weight_kg * 0.94, 2) if upgrade_eligibility.is_eligible else 0.0,
            basis="LIFECYCLE_EMISSION_BENCHMARK",
            assumptions=[
                "Upgraded specs keep hardware competitive with modern base-tier retail laptops",
            ],
        ),
        logistics=LogisticsEstimate(
            complexity="LOW",
            turnaround_days_min=1,
            turnaround_days_max=2,
            basis="SERVICE_BENCHMARK",
            assumptions=["Off-the-shelf standard PC components"],
        ),
        assumptions=[
            "Compatible firmware/BIOS supports drive capacity and memory density",
        ],
    )
    pathways.append(upgrade_pathway)

    # 3. REFURBISH
    refurbish_eligibility = evaluate_refurbish_eligibility(profile, specs)
    refurb_cost_min = cost_min + 30.0
    refurb_cost_max = cost_max + 55.0
    refurbish_pathway = PathwayOption(
        type=PathwayType.REFURBISH,
        title="Comprehensive Factory Refurbishment",
        summary="Complete teardown, ultrasonic cleaning, thermal overhaul, worn part replacement, and recertification.",
        eligibility=refurbish_eligibility,
        actions_required=[
            "Full chassis and internal ultrasonic cleaning",
            "Thermal repaste and fan bearing lubrication",
            "Battery cycle evaluation and replacement if under 80% health",
            "Factory fresh OS image and hardware diagnostic validation suite",
        ],
        estimated_cost=RangeEstimate(
            min_val=refurb_cost_min,
            max_val=refurb_cost_max,
            unit="INR",
            display_range=f"${int(refurb_cost_min)}–${int(refurb_cost_max)}",
            basis="DATABASE_ESTIMATE",
            assumptions=[
                "Refurbishment conducted by certified circular repair partner",
                "Includes 90-day warranty coverage",
            ],
        ),
        expected_life_extension_years=RangeEstimate(
            min_val=3.0,
            max_val=4.5,
            unit="years",
            display_range="+3–4.5 years",
            basis="MODEL_ESTIMATE",
            assumptions=[
                "Complete operational reset restores Grade A/B performance reliability",
            ],
        ),
        value_retained_percentage=88.0,
        material_retained_percentage=91.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=220.0,
            co2_avoided_kg_max=285.0,
            ewaste_diverted_kg=round(specs.weight_kg * 0.91, 2),
            basis="LIFECYCLE_EMISSION_BENCHMARK",
            assumptions=[
                "Prolongs whole system life across second commercial lifecycle",
            ],
        ),
        logistics=LogisticsEstimate(
            complexity="MODERATE",
            turnaround_days_min=3,
            turnaround_days_max=7,
            basis="SERVICE_BENCHMARK",
            assumptions=["Requires staging and diagnostic burn-in testing"],
        ),
        assumptions=[
            "Data backed up externally prior to disk re-imaging",
        ],
    )
    pathways.append(refurbish_pathway)

    # 4. REUSE / REDEPLOY
    reuse_eligibility = evaluate_reuse_redeploy_eligibility(profile, specs)
    reuse_pathway = PathwayOption(
        type=PathwayType.REUSE_REDEPLOY,
        title="Direct Second-Life Reuse / Redeployment",
        summary="Repurpose the existing functional hardware for student learning, Linux lab, or light productivity with minimal intervention.",
        eligibility=reuse_eligibility,
        actions_required=[
            "Secure disk erasure (NIST 800-88 compliant)",
            "Install lightweight OS (e.g. ChromeOS Flex, Ubuntu LTS, or clean Windows 11 SE)",
            "Deploy to secondary user / educational program",
        ],
        estimated_cost=RangeEstimate(
            min_val=0.0,
            max_val=20.0,
            unit="INR",
            display_range="₹0–₹20",
            basis="DATABASE_ESTIMATE",
            assumptions=[
                "Minimal physical intervention; software repurposing only",
            ],
        ),
        expected_life_extension_years=RangeEstimate(
            min_val=1.5,
            max_val=3.0,
            unit="years",
            display_range="+1.5–3 years",
            basis="MODEL_ESTIMATE",
            assumptions=[
                "Workload matched to remaining hardware capacity",
            ],
        ),
        value_retained_percentage=75.0,
        material_retained_percentage=100.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=240.0,
            co2_avoided_kg_max=295.0,
            ewaste_diverted_kg=specs.weight_kg,
            basis="LIFECYCLE_EMISSION_BENCHMARK",
            assumptions=[
                "Zero new components manufactured; 100% of embodied product carbon retained",
            ],
        ),
        logistics=LogisticsEstimate(
            complexity="LOW",
            turnaround_days_min=1,
            turnaround_days_max=2,
            basis="SERVICE_BENCHMARK",
            assumptions=["Software installation only"],
        ),
        assumptions=[
            "User accepts cosmetic signs of normal usage",
        ],
    )
    pathways.append(reuse_pathway)

    # 5. COMPONENT RECOVERY
    recovery_eligibility = evaluate_component_recovery_eligibility(profile, specs)
    recovery_pathway = PathwayOption(
        type=PathwayType.COMPONENT_RECOVERY,
        title="Modular Component Recovery & Harvest",
        summary="Salvage operational modular subcomponents (SSD, RAM, display panel, Wi-Fi card) for service spare inventory.",
        eligibility=recovery_eligibility,
        actions_required=[
            "Careful disassembly and harvest of functional modular parts",
            "SMART / functional bench validation of harvested components",
            "Cataloging into repair inventory; residue chassis routed to certified recycling",
        ],
        estimated_cost=RangeEstimate(
            min_val=15.0,
            max_val=35.0,
            unit="INR",
            display_range="₹15–₹35 (Disassembly & Testing)",
            basis="DATABASE_ESTIMATE",
            assumptions=[
                "Harvest labor offset by spare part inventory value (₹60–₹140 reclaimed value)",
            ],
        ),
        expected_life_extension_years=RangeEstimate(
            min_val=1.0,
            max_val=3.0,
            unit="years",
            display_range="+1–3 years (repurposed parts)",
            basis="MODEL_ESTIMATE",
            assumptions=[
                "Salvaged parts extend the life of multiple other devices in repair pool",
            ],
        ),
        value_retained_percentage=45.0,
        material_retained_percentage=60.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=80.0,
            co2_avoided_kg_max=130.0,
            ewaste_diverted_kg=round(specs.weight_kg * 0.60, 2),
            basis="LIFECYCLE_EMISSION_BENCHMARK",
            assumptions=[
                "Avoids manufacturing new replacement storage drives and memory chips",
            ],
        ),
        logistics=LogisticsEstimate(
            complexity="MODERATE",
            turnaround_days_min=2,
            turnaround_days_max=4,
            basis="SERVICE_BENCHMARK",
            assumptions=["Component testing required before inventory intake"],
        ),
        assumptions=[
            "Whole device computing is retired, but high-value subassemblies continue operating",
        ],
    )
    pathways.append(recovery_pathway)

    # 6. RECYCLE (Only when higher pathways are not viable)
    any_higher_eligible = (
        repair_eligibility.is_eligible
        or upgrade_eligibility.is_eligible
        or refurbish_eligibility.is_eligible
        or reuse_eligibility.is_eligible
        or recovery_eligibility.is_eligible
    )
    recycle_eligibility = evaluate_recycle_eligibility(profile, specs, any_higher_eligible)
    recycle_pathway = PathwayOption(
        type=PathwayType.RECYCLE,
        title="Responsible Material Recycling (WEEE)",
        summary="Material shredding and smelter reclamation of precious and base metals when functional reuse is exhausted.",
        eligibility=recycle_eligibility,
        actions_required=[
            "Hazardous battery de-energization and chemical recycling",
            "Mechanical separation of aluminum, copper, steel, and plastics",
            "Certified safe disposal of non-recoverable residues",
        ],
        estimated_cost=RangeEstimate(
            min_val=0.0,
            max_val=15.0,
            unit="INR",
            display_range="₹0–₹15",
            basis="DATABASE_ESTIMATE",
            assumptions=[
                "Drop-off at certified e-waste partner facility",
            ],
        ),
        expected_life_extension_years=RangeEstimate(
            min_val=0.0,
            max_val=0.0,
            unit="years",
            display_range="0 years (end of life)",
            basis="DATABASE_ESTIMATE",
            assumptions=[
                "Product ceases functional life; broken down to raw commodities",
            ],
        ),
        value_retained_percentage=5.0,
        material_retained_percentage=25.0,
        environmental_estimate=EnvironmentalEstimate(
            co2_avoided_kg_min=15.0,
            co2_avoided_kg_max=35.0,
            ewaste_diverted_kg=round(specs.weight_kg * 0.25, 2),
            basis="LIFECYCLE_EMISSION_BENCHMARK",
            assumptions=[
                "Reclaims secondary materials with high energy savings vs virgin extraction",
                "High loss of embodied product engineering value",
            ],
        ),
        logistics=LogisticsEstimate(
            complexity="LOW",
            turnaround_days_min=1,
            turnaround_days_max=3,
            basis="SERVICE_BENCHMARK",
            assumptions=["Standard e-waste drop-off"],
        ),
        assumptions=[
            "Recycling is strictly the final resort when higher circular loops are technically exhausted",
        ],
    )
    pathways.append(recycle_pathway)

    return pathways
