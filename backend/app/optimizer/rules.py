"""
Eligibility and constraint rules for circular pathways.
Contains ZERO AI dependencies — pure deterministic logic.
"""
from typing import Dict, List, Tuple
from app.schemas.enums import ComponentStatus, PathwayType
from app.schemas.condition import ConditionProfile
from app.schemas.product import ProductSpecs
from app.schemas.pathway import PathwayEligibility


def evaluate_repair_eligibility(
    profile: ConditionProfile, specs: ProductSpecs
) -> PathwayEligibility:
    reasons: List[str] = []
    ineligible_reasons: List[str] = []

    # Check if motherboard / system has critical non-repairable fault
    system_cond = profile.get_component("system")
    if system_cond and system_cond.status == ComponentStatus.REPLACE_REQUIRED:
        ineligible_reasons.append(
            "System board has critical irreparable fault; motherboard replacement exceeds device value."
        )

    # Check if any component needs repair/service/replacement
    repairable_needs: List[str] = []
    for comp_name in ["battery", "keyboard", "display", "thermals", "chassis"]:
        cond = profile.get_component(comp_name)
        if cond and cond.status in [ComponentStatus.SERVICE_REQUIRED, ComponentStatus.REPLACE_REQUIRED, ComponentStatus.FAIR]:
            if cond.repairable:
                repairable_needs.append(f"{comp_name} ({cond.label})")

    if not repairable_needs and not ineligible_reasons:
        ineligible_reasons.append("All components are already in good operational condition; standard repair not required.")
    elif repairable_needs:
        reasons.append(f"Identified serviceable/repairable items: {', '.join(repairable_needs)}.")

    is_eligible = len(ineligible_reasons) == 0 and len(repairable_needs) > 0
    return PathwayEligibility(
        is_eligible=is_eligible,
        reasons=reasons,
        ineligibility_reasons=ineligible_reasons,
    )


def evaluate_upgrade_eligibility(
    profile: ConditionProfile, specs: ProductSpecs
) -> PathwayEligibility:
    reasons: List[str] = []
    ineligible_reasons: List[str] = []

    # System board must be functional for whole-device upgrade
    system_cond = profile.get_component("system")
    if system_cond and system_cond.status == ComponentStatus.REPLACE_REQUIRED:
        ineligible_reasons.append("Base system logic board is not operational.")

    # Modularity check
    can_upgrade_ram = specs.ram_modular
    can_upgrade_ssd = specs.ssd_modular

    if not can_upgrade_ram and not can_upgrade_ssd:
        ineligible_reasons.append(
            "Both RAM and SSD storage are soldered to the logic board on this hardware model; hardware upgrades are non-viable."
        )
    else:
        upgrade_items = []
        if can_upgrade_ram:
            upgrade_items.append("Modular SO-DIMM RAM capacity")
        if can_upgrade_ssd:
            upgrade_items.append("M.2 NVMe SSD storage speed and capacity")
        reasons.append(f"Hardware architecture supports upgrades for: {', '.join(upgrade_items)}.")

    is_eligible = len(ineligible_reasons) == 0
    return PathwayEligibility(
        is_eligible=is_eligible,
        reasons=reasons,
        ineligibility_reasons=ineligible_reasons,
    )


def evaluate_refurbish_eligibility(
    profile: ConditionProfile, specs: ProductSpecs
) -> PathwayEligibility:
    reasons: List[str] = []
    ineligible_reasons: List[str] = []

    system_cond = profile.get_component("system")
    if system_cond and system_cond.status == ComponentStatus.REPLACE_REQUIRED:
        ineligible_reasons.append("Critical motherboard failure prevents complete device refurbishment.")

    display_cond = profile.get_component("display")
    chassis_cond = profile.get_component("chassis")

    cosmetic_or_thermal = (
        (profile.get_component("thermals") and profile.get_component("thermals").status != ComponentStatus.GOOD)
        or (chassis_cond and chassis_cond.status in [ComponentStatus.FAIR, ComponentStatus.SERVICE_REQUIRED])
        or (profile.get_component("battery") and profile.get_component("battery").status != ComponentStatus.GOOD)
    )

    if cosmetic_or_thermal:
        reasons.append("Device is suitable for comprehensive deep cleaning, thermal repasting, battery servicing, and cosmetic restoration to Grade A/B standard.")
    else:
        reasons.append("Device meets base criteria for standard factory refurbishment and recertification.")

    is_eligible = len(ineligible_reasons) == 0
    return PathwayEligibility(
        is_eligible=is_eligible,
        reasons=reasons,
        ineligibility_reasons=ineligible_reasons,
    )


def evaluate_reuse_redeploy_eligibility(
    profile: ConditionProfile, specs: ProductSpecs
) -> PathwayEligibility:
    reasons: List[str] = []
    ineligible_reasons: List[str] = []

    system_cond = profile.get_component("system")
    if system_cond and system_cond.status == ComponentStatus.REPLACE_REQUIRED:
        ineligible_reasons.append("System cannot POST or boot reliably.")

    ram_cond = profile.get_component("ram")
    if ram_cond and ram_cond.status == ComponentStatus.REPLACE_REQUIRED:
        ineligible_reasons.append("RAM failure prevents stable system execution without replacement.")

    display_cond = profile.get_component("display")
    if display_cond and display_cond.status == ComponentStatus.REPLACE_REQUIRED:
        ineligible_reasons.append("Display panel is shattered/inoperable; direct standalone reuse not viable without external monitor.")

    if not ineligible_reasons:
        reasons.append("Device retains working core architecture suitable for redeployment in education, light office, Linux learning, or secondary home computing.")

    is_eligible = len(ineligible_reasons) == 0
    return PathwayEligibility(
        is_eligible=is_eligible,
        reasons=reasons,
        ineligibility_reasons=ineligible_reasons,
    )


def evaluate_component_recovery_eligibility(
    profile: ConditionProfile, specs: ProductSpecs
) -> PathwayEligibility:
    reasons: List[str] = []
    ineligible_reasons: List[str] = []

    recoverable_parts = []
    ssd_cond = profile.get_component("ssd")
    if ssd_cond and ssd_cond.status in [ComponentStatus.GOOD, ComponentStatus.FAIR] and specs.ssd_modular:
        recoverable_parts.append(f"Modular SSD ({ssd_cond.label})")

    ram_cond = profile.get_component("ram")
    if ram_cond and ram_cond.status == ComponentStatus.GOOD and specs.ram_modular:
        recoverable_parts.append(f"Modular RAM sticks ({ram_cond.label})")

    display_cond = profile.get_component("display")
    if display_cond and display_cond.status in [ComponentStatus.GOOD, ComponentStatus.FAIR]:
        recoverable_parts.append("Display LCD panel assembly")

    battery_cond = profile.get_component("battery")
    if battery_cond and battery_cond.status in [ComponentStatus.GOOD, ComponentStatus.FAIR] and specs.battery_replaceable:
        recoverable_parts.append(f"Battery pack ({battery_cond.label})")

    if not recoverable_parts:
        ineligible_reasons.append("No viable high-value modular subcomponents remain salvageable.")
    else:
        reasons.append(f"Salvageable high-value components available for inventory: {', '.join(recoverable_parts)}.")

    is_eligible = len(recoverable_parts) > 0
    return PathwayEligibility(
        is_eligible=is_eligible,
        reasons=reasons,
        ineligibility_reasons=ineligible_reasons,
    )


def evaluate_recycle_eligibility(
    profile: ConditionProfile, specs: ProductSpecs, higher_pathways_viable: bool
) -> PathwayEligibility:
    """
    CRITICAL RULE from rules.md and prd.md:
    "Prefer repair/upgrade/refurbishment/reuse/component recovery before recycling when feasible."
    "Recycling when higher-value pathways are no longer technically/economically feasible."
    """
    reasons: List[str] = []
    ineligible_reasons: List[str] = []

    system_cond = profile.get_component("system")
    is_catastrophic = (
        system_cond and system_cond.status == ComponentStatus.REPLACE_REQUIRED
        and not specs.ram_modular
        and not specs.ssd_modular
    )

    if higher_pathways_viable and not is_catastrophic:
        ineligible_reasons.append(
            "Higher-value circular pathways (Repair, Upgrade, Refurbish, Reuse, or Component Recovery) are technically and economically viable. Premature material recycling destroys usable component value."
        )
    else:
        reasons.append(
            "Higher-value circular loops are exhausted or non-viable. Material recovery and certified WEEE recycling is appropriate to reclaim copper, aluminum, gold, and polymers."
        )

    is_eligible = not higher_pathways_viable or is_catastrophic
    return PathwayEligibility(
        is_eligible=is_eligible,
        reasons=reasons,
        ineligibility_reasons=ineligible_reasons,
    )
