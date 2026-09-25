"""
Report service coordinating unified condition reports and downloadable exports.
Combines product, condition profile, recommendations, alternative pathways,
impact estimates, assumptions, data gaps, disclaimer, and timestamps.
Reuses existing repositories and services without duplicating query logic.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.repositories import assessment_repo, product_repo, recommendation_repo
from app.db.store import store
from app.errors import AppError, ErrorCode
from app.schemas.enums import ComponentStatus
from app.schemas.recommendation import RecommendationRequest
from app.schemas.report import ConditionReportResponse, ReportImpactEstimates
from app.services.assessment_service import assessment_service
from app.services.product_service import product_service
from app.services.recommendation_service import recommendation_service


class ReportService:
    def get_report(
        self, assessment_id: str, db: Optional[Session] = None
    ) -> ConditionReportResponse:
        """
        Retrieves or builds the complete condition report combining product, condition profile,
        recommendation, alternatives, impact estimates, assumptions, and data gaps.
        Raises AppError(NOT_FOUND) if the assessment/product cannot be found.
        """
        # 1. Resolve Assessment Profile
        profile = None
        if db:
            profile = assessment_repo.get_by_id(db, assessment_id) or assessment_repo.get_by_product_id(db, assessment_id)
        if not profile:
            profile = store.get_profile(assessment_id)

        # If not found by assessment_id, check if identifier is a product_id or recommendation_id
        if not profile:
            rec = None
            if db:
                rec = recommendation_repo.get_by_id(db, assessment_id)
            if not rec:
                rec = store.get_recommendation(assessment_id)

            target_prod_id = rec.product_id if rec else assessment_id

            prod_exists = False
            if db and product_repo.get_by_id(db, target_prod_id):
                prod_exists = True
            elif store.get_product(target_prod_id):
                prod_exists = True

            if prod_exists:
                profile = assessment_service.build_profile(target_prod_id, db=db)

        if not profile:
            raise AppError(
                code=ErrorCode.NOT_FOUND.value,
                message=f"No assessment report found for ID '{assessment_id}'",
                field="assessment_id",
                http_status=404,
            )

        product_id = profile.product_id

        # 2. Resolve Product
        product = product_service.get_by_id(product_id, db=db)

        # 3. Resolve Recommendation
        recommendation = None
        if db:
            recommendation = recommendation_repo.get_by_product_id(db, product_id) or recommendation_repo.get_by_id(db, product_id)
        if not recommendation:
            recommendation = store.get_recommendation(product_id) or store.get_recommendation(assessment_id)

        if not recommendation:
            recommendation = recommendation_service.generate_recommendation(
                RecommendationRequest(product_id=product_id), db=db
            )

        # 4. Extract Impact Estimates
        primary = recommendation.primary_recommendation
        if primary and primary.pathway:
            p = primary.pathway
            env = p.environmental_estimate
            life = p.expected_life_extension_years
            cost = p.estimated_cost
            impact = ReportImpactEstimates(
                co2_avoided_kg_min=getattr(env, "co2_avoided_kg_min", 0.0),
                co2_avoided_kg_max=getattr(env, "co2_avoided_kg_max", 0.0),
                ewaste_diverted_kg=getattr(env, "ewaste_diverted_kg", 0.0),
                life_extension_years_min=getattr(life, "min_val", 0.0),
                life_extension_years_max=getattr(life, "max_val", 0.0),
                estimated_cost_min=getattr(cost, "min_val", 0.0),
                estimated_cost_max=getattr(cost, "max_val", 0.0),
                value_retained_percentage=getattr(p, "value_retained_percentage", 0.0),
                material_retained_percentage=getattr(p, "material_retained_percentage", 0.0),
            )
        else:
            impact = ReportImpactEstimates()

        # 5. Compile all assumptions
        assumptions_list = []
        if recommendation.assumptions:
            assumptions_list.extend(recommendation.assumptions)
        if recommendation.explicit_assumptions:
            assumptions_list.extend(recommendation.explicit_assumptions)
        if primary and primary.pathway and primary.pathway.assumptions:
            assumptions_list.extend(primary.pathway.assumptions)
        # Deduplicate while preserving order
        deduped_assumptions = list(dict.fromkeys([a for a in assumptions_list if a]))

        # 6. Identify Data Gaps (components with UNKNOWN status or insufficient evidence)
        data_gaps: List[str] = []
        for comp_name, cond in profile.components.items():
            if cond.status == ComponentStatus.UNKNOWN or any("Insufficient evidence" in str(obs) for obs in cond.observations):
                obs_snippet = cond.observations[0] if cond.observations else "No diagnostic uploaded"
                data_gaps.append(f"{comp_name.upper()}: {cond.label} — {obs_snippet}")

        # 7. Ensure explanation exists
        if not recommendation.explanation:
            from app.services.explanation_service import explanation_service
            recommendation.explanation = explanation_service.generate_guarded_explanation(
                product=product,
                recommendation=recommendation,
                profile=profile,
            )

        # 8. Construct and return ConditionReportResponse
        return ConditionReportResponse(
            id=assessment_id,
            assessment_id=assessment_id,
            product_id=product_id,
            product=product,
            condition_profile=profile,
            recommendation=recommendation,
            alternative_pathways=recommendation.alternative_pathways or [],
            impact_estimates=impact,
            assumptions=deduped_assumptions,
            data_gaps=data_gaps,
            explanation=recommendation.explanation,
            disclaimer="Demo baseline assumptions, not verified market data. Estimates are derived from deterministic model parameters.",
            timestamp=profile.created_at,
        )


report_service = ReportService()
