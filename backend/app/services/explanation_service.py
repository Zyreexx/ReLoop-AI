"""
Explanation service providing guarded narrative explanations for circular recommendations.
Enforces:
1. Strict post-generation numeric guardrail: rejects any AI output introducing numbers not present in supplied data.
2. Deterministic template fallback on guardrail rejection, Gemini failure, or offline mode.
3. Immutability: explanation never mutates deterministic pathway selection or scores.
4. Provenance tracking with source: "ai" | "template".
"""
import logging
import re
from typing import Any, List, Optional, Set

from app.ai.gemini_client import gemini_client
from app.ai.schemas import ExplanationOutput
from app.schemas.condition import ConditionProfile
from app.schemas.recommendation import Recommendation, RecommendationExplanation

logger = logging.getLogger(__name__)

# Matches integer or decimal numbers (e.g. 5420, 73, 4.5, 0.73, 16 in 16GB)
NUMBER_REGEX = re.compile(r"\d+(?:\.\d+)?")


def normalize_number(num_str: str) -> Optional[float]:
    try:
        val = float(num_str)
        return round(val, 4)
    except (ValueError, TypeError):
        return None


def extract_numbers_from_text(text: str) -> Set[float]:
    if not text:
        return set()
    cleaned = text.replace(",", "")
    matches = NUMBER_REGEX.findall(cleaned)
    nums = set()
    for m in matches:
        n = normalize_number(m)
        if n is not None:
            nums.add(n)
            if n.is_integer():
                nums.add(float(int(n)))
    return nums


def collect_numbers_from_obj(obj: Any, visited: Optional[Set[int]] = None) -> Set[float]:
    if visited is None:
        visited = set()
    if id(obj) in visited:
        return set()
    visited.add(id(obj))

    nums: Set[float] = set()

    if obj is None:
        return nums

    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        val = float(obj)
        nums.add(round(val, 4))
        if val.is_integer():
            nums.add(float(int(val)))
        if 0.0 <= val <= 1.0:
            pct = round(val * 100.0, 2)
            nums.add(pct)
            if pct.is_integer():
                nums.add(float(int(pct)))
        return nums

    if isinstance(obj, str):
        nums.update(extract_numbers_from_text(obj))
        return nums

    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                nums.update(extract_numbers_from_text(k))
            nums.update(collect_numbers_from_obj(v, visited))
        return nums

    if isinstance(obj, (list, tuple, set)):
        for item in obj:
            nums.update(collect_numbers_from_obj(item, visited))
        return nums

    if hasattr(obj, "model_dump"):
        try:
            dumped = obj.model_dump()
            nums.update(collect_numbers_from_obj(dumped, visited))
        except Exception:
            pass

    if hasattr(obj, "__dict__"):
        nums.update(collect_numbers_from_obj(obj.__dict__, visited))

    return nums


def validate_explanation_numbers(
    explanation: ExplanationOutput | RecommendationExplanation,
    allowed_numbers: Set[float],
) -> bool:
    """
    Returns True if every number appearing in summary, details, and assumptions
    is present in allowed_numbers. Returns False if any unknown number is introduced.
    """
    text_corpus = (
        explanation.summary
        + " "
        + " ".join(explanation.details)
        + " "
        + " ".join(explanation.assumptions)
    )
    found_numbers = extract_numbers_from_text(text_corpus)

    unverified_numbers = []
    for n in found_numbers:
        if not any(abs(n - allowed) < 1e-4 for allowed in allowed_numbers):
            unverified_numbers.append(n)

    if unverified_numbers:
        logger.warning(
            f"AI explanation guardrail triggered: rejected output introducing unverified numbers {unverified_numbers}"
        )
        return False

    return True


def build_template_explanation(
    product: Any,
    recommendation: Recommendation,
    profile: Optional[ConditionProfile] = None,
) -> RecommendationExplanation:
    """
    Builds a deterministic, human-readable template explanation directly from verified data.
    """
    pathway_str = (
        recommendation.selected_pathway.value
        if hasattr(recommendation.selected_pathway, "value")
        else str(recommendation.selected_pathway)
    )
    obj_str = (
        recommendation.objective.value
        if hasattr(recommendation.objective, "value")
        else str(recommendation.objective)
    )
    obj_display = obj_str.replace("_", " ").title()

    prod_name = (
        f"{getattr(product, 'manufacturer', '')} {getattr(product, 'model', '')}".strip()
        or "Device"
    )

    primary = recommendation.primary_recommendation
    p = primary.pathway if primary else None

    # Construct clean summary
    summary = (
        f"Based on verified diagnostic and optical condition data, {pathway_str.replace('_', ' ').upper()} was "
        f"selected for {prod_name} under the {obj_display} objective."
    )

    details: List[str] = []
    if p:
        cost = p.estimated_cost
        life = p.expected_life_extension_years
        env = p.environmental_estimate

        details.append(
            f"Expected useful life extension: {life.min_val:g}–{life.max_val:g} years (modeled estimate)."
        )
        details.append(
            f"Estimated pathway cost: ₹{cost.min_val:g} – ₹{cost.max_val:g}."
        )
        details.append(
            f"Environmental impact: {env.co2_avoided_kg_min:g}–{env.co2_avoided_kg_max:g} kg CO2e avoided "
            f"with {env.ewaste_diverted_kg:g} kg e-waste diverted."
        )

    # Add top reasoning bullets from deterministic engine
    if recommendation.reasoning:
        for r in recommendation.reasoning[:3]:
            if r not in details:
                details.append(r)

    # Compile assumptions
    assumptions_list = []
    if recommendation.assumptions:
        assumptions_list.extend(recommendation.assumptions)
    if recommendation.explicit_assumptions:
        assumptions_list.extend(recommendation.explicit_assumptions)
    if p and p.assumptions:
        assumptions_list.extend(p.assumptions)

    deduped_assumptions = list(dict.fromkeys([a for a in assumptions_list if a]))

    return RecommendationExplanation(
        summary=summary,
        details=details,
        assumptions=deduped_assumptions,
        source="template",
    )


class ExplanationService:
    def generate_guarded_explanation(
        self,
        product: Any,
        recommendation: Recommendation,
        profile: Optional[ConditionProfile] = None,
    ) -> RecommendationExplanation:
        """
        Coordinates AI explanation generation with strict post-generation numeric guardrails.
        - AI explanation is attempted if Gemini is configured/mocked.
        - If AI introduces any unverified numbers, or fails/raises, falls back to deterministic template explanation.
        - NEVER modifies recommendation.selected_pathway, recommendation.score, or alternative_pathways.
        """
        # 1. Generate template explanation baseline
        template_exp = build_template_explanation(product, recommendation, profile)

        # 2. Format context for AI
        pathway_str = (
            recommendation.selected_pathway.value
            if hasattr(recommendation.selected_pathway, "value")
            else str(recommendation.selected_pathway)
        )
        obj_str = (
            recommendation.objective.value
            if hasattr(recommendation.objective, "value")
            else str(recommendation.objective)
        )
        prod_name = (
            f"{getattr(product, 'manufacturer', '')} {getattr(product, 'model', '')}".strip()
            or "Device"
        )

        primary = recommendation.primary_recommendation
        p = primary.pathway if primary else None

        life_str = (
            f"{p.expected_life_extension_years.min_val}–{p.expected_life_extension_years.max_val} years"
            if p
            else "2-3 years"
        )
        cost_str = (
            f"₹{p.estimated_cost.min_val}–₹{p.estimated_cost.max_val}"
            if p
            else "Standard repair cost"
        )
        co2_str = (
            f"{p.environmental_estimate.co2_avoided_kg_min}–{p.environmental_estimate.co2_avoided_kg_max} kg"
            if p
            else "100-150 kg"
        )

        evidence_bullets = []
        if profile and profile.components:
            for comp_name, comp in profile.components.items():
                st = comp.status.value if hasattr(comp.status, "value") else str(comp.status)
                obs = "; ".join(comp.observations) if comp.observations else ""
                evidence_bullets.append(f"- {comp_name.upper()}: {st} ({comp.label}) {obs}".strip())
        evidence_summary = "\n".join(evidence_bullets) if evidence_bullets else "Standard hardware condition"

        # 3. Collect all allowed numbers
        allowed_numbers = collect_numbers_from_obj({
            "product": product,
            "recommendation": recommendation,
            "profile": profile,
            "evidence_summary": evidence_summary,
            "life_extension": life_str,
            "cost": cost_str,
            "co2_avoided": co2_str,
            "pathway": pathway_str,
            "objective": obj_str,
        })

        # 4. Attempt AI explanation
        try:
            ai_output = gemini_client.generate_explanation(
                pathway=pathway_str,
                model=prod_name,
                objective=obj_str,
                evidence_summary=evidence_summary,
                life_extension=life_str,
                cost=cost_str,
                co2_avoided=co2_str,
            )

            if ai_output and isinstance(ai_output, ExplanationOutput):
                # 5. Apply post-generation numeric guardrail
                is_valid = validate_explanation_numbers(ai_output, allowed_numbers)
                if is_valid:
                    return RecommendationExplanation(
                        summary=ai_output.summary,
                        details=ai_output.details or template_exp.details,
                        assumptions=ai_output.assumptions or template_exp.assumptions,
                        source="ai",
                    )
                else:
                    logger.warning(
                        "AI explanation rejected due to unverified numbers; using template fallback."
                    )
                    return template_exp

        except Exception as e:
            logger.info(
                f"AI explanation generation unavailable or failed ({e}); using template fallback."
            )

        return template_exp


explanation_service = ExplanationService()
