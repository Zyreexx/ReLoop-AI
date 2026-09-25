"""
Tests for the deterministic Circular Path Optimizer.
Verifies rules, zero AI coupling, determinism, and multi-objective ranking.
"""
import sys
from app.schemas.enums import ObjectiveType, PathwayType, ComponentStatus
from app.schemas.product import ProductRecord, ProductSpecs, DeviceCategory
from app.schemas.condition import ComponentCondition, ConditionProfile
from app.optimizer.scorer import score_pathways
from app.optimizer.rules import evaluate_upgrade_eligibility, evaluate_recycle_eligibility


def test_optimizer_has_no_ai_imports():
    """
    CRITICAL NON-NEGOTIABLE RULE:
    The optimizer in backend/app/optimizer/ is plain deterministic Python
    and imports nothing from app/ai/.
    """
    import inspect
    import app.optimizer.scorer as scorer
    import app.optimizer.rules as rules
    import app.optimizer.pathways as pathways

    for mod in [scorer, rules, pathways]:
        source = inspect.getsource(mod)
        assert "from app.ai" not in source, f"{mod.__name__} violates rule: imports from app.ai"
        assert "import app.ai" not in source, f"{mod.__name__} violates rule: imports app.ai"
        assert "gemini" not in source.lower(), f"{mod.__name__} references gemini"


def test_scoring_determinism(dell_latitude_5420, repairable_condition_profile):
    """
    Scoring must be 100% deterministic and reproducible.
    Identical inputs must yield identical scores and rankings across repeated runs.
    """
    result_1 = score_pathways(dell_latitude_5420, repairable_condition_profile, ObjectiveType.MAXIMUM_LIFE)
    result_2 = score_pathways(dell_latitude_5420, repairable_condition_profile, ObjectiveType.MAXIMUM_LIFE)

    assert result_1.selected_pathway == result_2.selected_pathway
    assert result_1.primary_recommendation.score == result_2.primary_recommendation.score
    assert len(result_1.alternative_pathways) == len(result_2.alternative_pathways)

    for p1, p2 in zip(result_1.alternative_pathways, result_2.alternative_pathways):
        assert p1.pathway.type == p2.pathway.type
        assert p1.score == p2.score
        assert p1.rank == p2.rank


def test_repairable_canonical_demo_recommends_repair(dell_latitude_5420, repairable_condition_profile):
    """
    Demo device from memory.md:
    Battery (73%), Keyboard damage, healthy SSD (91%), passing RAM, thermal throttling.
    Expected outcome: REPAIR or REFURBISH is selected, while SSD/RAM are retained.
    """
    res = score_pathways(dell_latitude_5420, repairable_condition_profile, ObjectiveType.MAXIMUM_LIFE)
    assert res.selected_pathway in [PathwayType.REPAIR, PathwayType.REFURBISH]
    assert res.primary_recommendation.score > 70.0

    # Ensure evidence IDs from battery, thermals, ssd are linked in reasoning
    assert len(res.linked_evidence_ids) > 0
    assert any("Battery" in r for r in res.reasoning)
    assert any("storage" in r.lower() or "ssd" in r.lower() for r in res.reasoning)


def test_lowest_cost_objective_prioritizes_low_cost(dell_latitude_5420, repairable_condition_profile):
    """
    Under LOWEST_COST objective, low-expenditure pathways should be strongly weighted.
    """
    res_cost = score_pathways(dell_latitude_5420, repairable_condition_profile, ObjectiveType.LOWEST_COST)
    res_life = score_pathways(dell_latitude_5420, repairable_condition_profile, ObjectiveType.MAXIMUM_LIFE)

    assert res_cost.objective == ObjectiveType.LOWEST_COST
    # Compare ranks / scores of low cost vs high cost
    cost_subscore = res_cost.primary_recommendation.normalized_subscores["cost_economy"]
    assert cost_subscore > 0.5


def test_soldered_model_ineligible_for_upgrade():
    """
    When RAM and SSD are soldered (e.g. MacBook Pro), UPGRADE must be marked ineligible
    with an explicit technical reason.
    """
    soldered_mac = ProductRecord(
        manufacturer="Apple",
        model="MacBook Pro 13-inch (2019)",
        model_year=2019,
        category=DeviceCategory.LAPTOP,
        specs=ProductSpecs(ram_modular=False, ssd_modular=False, battery_replaceable=False),
    )
    profile = ConditionProfile(
        product_id=soldered_mac.id,
        components={
            "system": ComponentCondition(component="system", status=ComponentStatus.GOOD, label="Good"),
            "ram": ComponentCondition(component="ram", status=ComponentStatus.GOOD, label="8GB LPDDR3"),
            "ssd": ComponentCondition(component="ssd", status=ComponentStatus.GOOD, label="256GB"),
        },
    )

    eligibility = evaluate_upgrade_eligibility(profile, soldered_mac.specs)
    assert eligibility.is_eligible is False
    assert any("soldered" in r.lower() for r in eligibility.ineligibility_reasons)


def test_recycle_is_ineligible_when_higher_loops_viable(dell_latitude_5420, repairable_condition_profile):
    """
    NON-NEGOTIABLE RULE:
    Prefer repair/upgrade/refurbishment/reuse/component recovery before recycling when feasible.
    Recycle should not be eligible if higher pathways are viable.
    """
    eligibility = evaluate_recycle_eligibility(repairable_condition_profile, dell_latitude_5420.specs, higher_pathways_viable=True)
    assert eligibility.is_eligible is False
    assert any("Higher-value circular pathways" in r for r in eligibility.ineligibility_reasons)


def test_recycle_is_eligible_for_catastrophic_failure():
    """
    When whole system is dead and no modular components are salvageable,
    recycling is the appropriate final pathway.
    """
    catastrophic_specs = ProductSpecs(ram_modular=False, ssd_modular=False, battery_replaceable=False)
    profile = ConditionProfile(
        product_id="dead_laptop",
        components={
            "system": ComponentCondition(component="system", status=ComponentStatus.REPLACE_REQUIRED, label="Dead"),
        },
    )
    eligibility = evaluate_recycle_eligibility(profile, catastrophic_specs, higher_pathways_viable=False)
    assert eligibility.is_eligible is True
