"""
Golden regression and property tests for the Circular Pathway Optimizer.
Enforces:
1. Exact match against golden fixtures for all 4 demo cases across 4 optimization objectives (16 matrix points).
2. Pure determinism property: Repeated executions on identical inputs produce bit-identical recommendations.
3. Component permutation invariance property: Reordering condition profile components has zero effect on outcome.
4. Ineligible pathway sorting property: Ineligible pathways are always sorted after eligible pathways and never selected when eligible options exist.
"""
import json
import random
from pathlib import Path
import pytest

from app.knowledge import get_demo_data_dir
from app.optimizer.scorer import score_pathways
from app.schemas.condition import ComponentCondition, ConditionProfile
from app.schemas.enums import ComponentStatus, DeviceCategory, Objective, PathwayType
from app.schemas.product import ProductRecord, ProductSpecs

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

OBJECTIVES = [
    Objective.LOWEST_COST,
    Objective.MAX_LIFE,
    Objective.ENVIRONMENTAL,
    Objective.FASTEST_RECOVERY,
]

DEMO_STEMS = [
    "demo_01_healthy",
    "demo_02_repairable",
    "demo_03_borderline",
    "demo_04_component_recovery",
]


def load_demo_case_input(file_stem: str):
    """Loads demo case JSON from data/demo/ and builds ProductRecord and ConditionProfile."""
    demo_dir = get_demo_data_dir()
    json_path = demo_dir / f"{file_stem}.json"
    assert json_path.exists(), f"Demo file {json_path} not found"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

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


def load_golden_fixture(file_stem: str):
    """Loads golden expectation JSON from tests/golden/."""
    fixture_path = GOLDEN_DIR / f"{file_stem}.json"
    assert fixture_path.exists(), f"Golden fixture {fixture_path} not found"
    with open(fixture_path, "r", encoding="utf-8") as f:
        return json.load(f)


# --- 1. Golden Fixture Regression Tests ---

@pytest.mark.parametrize("file_stem", DEMO_STEMS)
@pytest.mark.parametrize("objective", OBJECTIVES)
def test_optimizer_matches_golden_fixture(file_stem: str, objective: Objective):
    """
    Reruns the circular optimizer for the given demo case and objective,
    asserting an exact match against the locked golden fixture.
    """
    product, profile, _ = load_demo_case_input(file_stem)
    golden = load_golden_fixture(file_stem)

    obj_key = objective.value
    expected = golden["objectives"][obj_key]

    rec = score_pathways(product, profile, objective)

    # 1. Verify primary selected pathway
    assert rec.selected_pathway.value == expected["selected_pathway"], (
        f"Selected pathway mismatch for {file_stem} under {obj_key}: "
        f"got {rec.selected_pathway.value}, expected {expected['selected_pathway']}"
    )

    # 2. Verify primary score
    assert rec.score == pytest.approx(expected["primary_score"], abs=0.1), (
        f"Primary score mismatch for {file_stem} under {obj_key}: "
        f"got {rec.score}, expected {expected['primary_score']}"
    )

    # 3. Verify full ranked order of pathways
    actual_ranking = [rec.primary_recommendation.pathway.type.value] + [
        alt.pathway.type.value for alt in rec.alternative_pathways
    ]
    assert actual_ranking == expected["ranked_pathways"], (
        f"Ranked pathway order mismatch for {file_stem} under {obj_key}: "
        f"got {actual_ranking}, expected {expected['ranked_pathways']}"
    )

    # 4. Verify each scored pathway in the ranking
    actual_scores = [rec.primary_recommendation.score] + [
        alt.score for alt in rec.alternative_pathways
    ]
    for i, exp_scored in enumerate(expected["scored_ranking"]):
        assert actual_ranking[i] == exp_scored["pathway"]
        assert actual_scores[i] == pytest.approx(exp_scored["score"], abs=0.1)


# --- 2. Property Tests ---

@pytest.mark.parametrize("file_stem", DEMO_STEMS)
@pytest.mark.parametrize("objective", OBJECTIVES)
def test_property_pure_determinism(file_stem: str, objective: Objective):
    """
    Property 1: Pure Determinism.
    Running the optimizer on identical inputs twice produces identical outputs.
    """
    product, profile, _ = load_demo_case_input(file_stem)

    run_1 = score_pathways(product, profile, objective)
    run_2 = score_pathways(product, profile, objective)

    assert run_1.selected_pathway == run_2.selected_pathway
    assert run_1.score == run_2.score
    assert len(run_1.alternative_pathways) == len(run_2.alternative_pathways)

    for a1, a2 in zip(run_1.alternative_pathways, run_2.alternative_pathways):
        assert a1.pathway.type == a2.pathway.type
        assert a1.score == a2.score
        assert a1.rank == a2.rank
        assert a1.pathway.eligibility.is_eligible == a2.pathway.eligibility.is_eligible


@pytest.mark.parametrize("file_stem", DEMO_STEMS)
@pytest.mark.parametrize("objective", OBJECTIVES)
def test_property_component_order_invariance(file_stem: str, objective: Objective):
    """
    Property 2: Permutation Invariance.
    Reordering the items in profile.components dictionary must have zero effect on scores or rankings.
    """
    product, profile, _ = load_demo_case_input(file_stem)

    # Baseline run
    baseline = score_pathways(product, profile, objective)

    # Permuted runs: reverse order and random shuffled order
    comp_items = list(profile.components.items())

    # Reversed order
    reversed_profile = ConditionProfile(
        product_id=product.id,
        components=dict(reversed(comp_items)),
    )
    res_reversed = score_pathways(product, reversed_profile, objective)

    assert res_reversed.selected_pathway == baseline.selected_pathway
    assert res_reversed.score == baseline.score
    assert [p.pathway.type for p in res_reversed.alternative_pathways] == [
        p.pathway.type for p in baseline.alternative_pathways
    ]

    # Shuffled order
    rng = random.Random(42)
    shuffled_items = list(comp_items)
    rng.shuffle(shuffled_items)

    shuffled_profile = ConditionProfile(
        product_id=product.id,
        components=dict(shuffled_items),
    )
    res_shuffled = score_pathways(product, shuffled_profile, objective)

    assert res_shuffled.selected_pathway == baseline.selected_pathway
    assert res_shuffled.score == baseline.score
    assert [p.pathway.type for p in res_shuffled.alternative_pathways] == [
        p.pathway.type for p in baseline.alternative_pathways
    ]


@pytest.mark.parametrize("file_stem", DEMO_STEMS)
@pytest.mark.parametrize("objective", OBJECTIVES)
def test_property_ineligible_pathways_rank_below_eligible(file_stem: str, objective: Objective):
    """
    Property 3: Ineligible Pathway Behavior.
    - An ineligible pathway is never chosen as the primary selected_pathway when eligible options exist.
    - In the ranked output, all eligible pathways appear before any ineligible pathway.
    """
    product, profile, _ = load_demo_case_input(file_stem)
    rec = score_pathways(product, profile, objective)

    all_scored = [rec.primary_recommendation] + list(rec.alternative_pathways)

    seen_ineligible = False
    for scored_item in all_scored:
        is_eligible = scored_item.pathway.eligibility.is_eligible
        if not is_eligible:
            seen_ineligible = True
        else:
            # If we see an eligible pathway AFTER having seen an ineligible one, the sorting invariant was violated
            assert not seen_ineligible, (
                f"Eligible pathway {scored_item.pathway.type} ranked after an ineligible pathway "
                f"in {file_stem} under {objective.value}"
            )

    # Primary recommendation must be eligible if any pathway in the set is eligible
    any_eligible = any(s.pathway.eligibility.is_eligible for s in all_scored)
    if any_eligible:
        assert rec.primary_recommendation.pathway.eligibility.is_eligible is True
