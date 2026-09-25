"""
Verification of the 4 canonical demo scenarios specified in rules.md (section 12):
1. Healthy-ish device (direct reuse / redeployment)
2. Repairable device (targeted component repair)
3. Borderline device (upgrade / refurbish evaluation)
4. Component recovery device (failed board, modular parts salvaged)
"""
from app.schemas.enums import ObjectiveType, PathwayType, ComponentStatus, DeviceCategory
from app.schemas.product import ProductRecord, ProductSpecs
from app.schemas.condition import ComponentCondition, ConditionProfile
from app.optimizer.scorer import score_pathways


def test_case_1_healthy_device_prioritizes_reuse():
    """
    Case 1: 3-year-old ThinkPad T490 with 92% battery, 98% SSD, pass RAM, clean thermals.
    Recommendation: REUSE_REDEPLOY or UPGRADE.
    """
    prod = ProductRecord(
        manufacturer="Lenovo",
        model="ThinkPad T490",
        model_year=2021,
        specs=ProductSpecs(ram_modular=True, ssd_modular=True, battery_replaceable=True),
    )
    profile = ConditionProfile(
        product_id=prod.id,
        components={
            "battery": ComponentCondition(component="battery", status=ComponentStatus.GOOD, label="92% Healthy"),
            "ssd": ComponentCondition(component="ssd", status=ComponentStatus.GOOD, label="98% Healthy", upgradeable=True),
            "ram": ComponentCondition(component="ram", status=ComponentStatus.GOOD, label="PASS", upgradeable=True),
            "thermals": ComponentCondition(component="thermals", status=ComponentStatus.GOOD, label="Normal (<70°C)"),
            "display": ComponentCondition(component="display", status=ComponentStatus.GOOD, label="Clean"),
            "keyboard": ComponentCondition(component="keyboard", status=ComponentStatus.GOOD, label="Intact"),
            "chassis": ComponentCondition(component="chassis", status=ComponentStatus.GOOD, label="Light wear"),
            "system": ComponentCondition(component="system", status=ComponentStatus.GOOD, label="POST OK"),
        },
    )

    rec = score_pathways(prod, profile, ObjectiveType.LOWEST_COST)
    assert rec.selected_pathway in [PathwayType.REUSE_REDEPLOY, PathwayType.UPGRADE]


def test_case_2_repairable_device_recommends_repair():
    """
    Case 2: 4-year-old Dell Latitude 5420:
    Battery (73%), Missing keyboard keycap, 96°C thermal throttling, healthy SSD & RAM.
    Recommendation: REPAIR or REFURBISH.
    """
    prod = ProductRecord(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        specs=ProductSpecs(ram_modular=True, ssd_modular=True, battery_replaceable=True),
    )
    profile = ConditionProfile(
        product_id=prod.id,
        components={
            "battery": ComponentCondition(component="battery", status=ComponentStatus.SERVICE_REQUIRED, label="73% Health", repairable=True),
            "ssd": ComponentCondition(component="ssd", status=ComponentStatus.GOOD, label="91% Healthy"),
            "ram": ComponentCondition(component="ram", status=ComponentStatus.GOOD, label="PASS"),
            "thermals": ComponentCondition(component="thermals", status=ComponentStatus.SERVICE_REQUIRED, label="Throttling", repairable=True),
            "display": ComponentCondition(component="display", status=ComponentStatus.GOOD, label="Clean"),
            "keyboard": ComponentCondition(component="keyboard", status=ComponentStatus.SERVICE_REQUIRED, label="Missing Key", repairable=True),
            "chassis": ComponentCondition(component="chassis", status=ComponentStatus.FAIR, label="Moderate wear"),
            "system": ComponentCondition(component="system", status=ComponentStatus.GOOD, label="POST OK"),
        },
    )

    rec = score_pathways(prod, profile, ObjectiveType.MAXIMUM_LIFE)
    assert rec.selected_pathway in [PathwayType.REPAIR, PathwayType.REFURBISH]
    assert rec.primary_recommendation.score > 60.0


def test_case_3_borderline_device():
    """
    Case 3: HP EliteBook 840 G6 with multiple aged components.
    Evaluates refurbishment vs targeted repair vs second life.
    """
    prod = ProductRecord(
        manufacturer="HP",
        model="EliteBook 840 G6",
        model_year=2019,
        specs=ProductSpecs(ram_modular=True, ssd_modular=True, battery_replaceable=True),
    )
    profile = ConditionProfile(
        product_id=prod.id,
        components={
            "battery": ComponentCondition(component="battery", status=ComponentStatus.FAIR, label="76% Health", repairable=True),
            "ssd": ComponentCondition(component="ssd", status=ComponentStatus.FAIR, label="68% Health", upgradeable=True),
            "ram": ComponentCondition(component="ram", status=ComponentStatus.GOOD, label="PASS", upgradeable=True),
            "thermals": ComponentCondition(component="thermals", status=ComponentStatus.SERVICE_REQUIRED, label="Throttling", repairable=True),
            "display": ComponentCondition(component="display", status=ComponentStatus.GOOD, label="Clean"),
            "keyboard": ComponentCondition(component="keyboard", status=ComponentStatus.GOOD, label="Good"),
            "chassis": ComponentCondition(component="chassis", status=ComponentStatus.FAIR, label="Fair"),
            "system": ComponentCondition(component="system", status=ComponentStatus.GOOD, label="POST OK"),
        },
    )

    rec = score_pathways(prod, profile, ObjectiveType.ENVIRONMENTAL_BENEFIT)
    assert rec.selected_pathway in [PathwayType.REFURBISH, PathwayType.REPAIR, PathwayType.UPGRADE, PathwayType.REUSE_REDEPLOY]
    assert rec.primary_recommendation.score > 60.0


def test_case_4_component_recovery_device():
    """
    Case 4: Failed motherboard / liquid damaged logic board,
    but modular 1TB NVMe SSD, 32GB RAM sticks, and intact 1080p display panel.
    Recommendation: COMPONENT_RECOVERY.
    """
    prod = ProductRecord(
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        specs=ProductSpecs(ram_modular=True, ssd_modular=True, battery_replaceable=True),
    )
    profile = ConditionProfile(
        product_id=prod.id,
        components={
            "battery": ComponentCondition(component="battery", status=ComponentStatus.UNKNOWN, label="Untested"),
            "ssd": ComponentCondition(component="ssd", status=ComponentStatus.GOOD, label="1TB NVMe — 98% SMART Health"),
            "ram": ComponentCondition(component="ram", status=ComponentStatus.GOOD, label="32GB DDR4 Tested Pass"),
            "thermals": ComponentCondition(component="thermals", status=ComponentStatus.UNKNOWN, label="Inoperable"),
            "display": ComponentCondition(component="display", status=ComponentStatus.GOOD, label="Intact Panel"),
            "keyboard": ComponentCondition(component="keyboard", status=ComponentStatus.UNKNOWN, label="Liquid residue"),
            "chassis": ComponentCondition(component="chassis", status=ComponentStatus.FAIR, label="Chassis intact"),
            "system": ComponentCondition(component="system", status=ComponentStatus.REPLACE_REQUIRED, label="Dead / Won't POST"),
        },
    )

    rec = score_pathways(prod, profile, ObjectiveType.MAXIMUM_LIFE)
    assert rec.selected_pathway == PathwayType.COMPONENT_RECOVERY
    assert rec.component_recovery is not None
    assert len(rec.component_recovery.recoverable_parts) >= 2
