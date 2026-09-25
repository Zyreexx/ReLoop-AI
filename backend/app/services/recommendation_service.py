"""
Recommendation service coordinating deterministic optimization and reporting.
Enforces the boundary: The deterministic optimizer in app.optimizer produces the scores;
AI is only used for narrative explanation if requested.
"""
from typing import Optional
from sqlalchemy.orm import Session
from app.db.repositories import (
    product_repo,
    assessment_repo,
    recommendation_repo,
)
from app.db.store import store
from app.optimizer.scorer import score_pathways
from app.schemas.enums import ObjectiveType, Objective
from app.schemas.errors import AppException
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.assessment_service import assessment_service


class RecommendationService:
    def generate_recommendation(
        self, req: RecommendationRequest, db: Optional[Session] = None
    ) -> RecommendationResponse:
        product = store.get_product(req.product_id)
        if not product and db:
            product = product_repo.get_by_id(db, req.product_id)

        if not product:
            raise AppException(
                code="PRODUCT_NOT_FOUND",
                message=f"No product registered with ID '{req.product_id}'",
                field="product_id",
                status_code=404,
            )

        # Retrieve or build condition profile
        profile = store.get_profile(req.product_id)
        if not profile and db:
            profile = assessment_repo.get_by_product_id(db, req.product_id)
        if not profile:
            profile = assessment_service.build_profile(req.product_id, db=db)

        # Deterministic scoring
        rec = score_pathways(
            product=product,
            profile=profile,
            objective=req.objective or Objective.MAX_LIFE,
        )

        # Generate guarded narrative explanation (AI with template fallback)
        from app.services.explanation_service import explanation_service
        rec.explanation = explanation_service.generate_guarded_explanation(
            product=product,
            recommendation=rec,
            profile=profile,
        )

        # Save to database and memory store
        if db:
            recommendation_repo.save(db, rec)
        store.save_recommendation(rec)
        return rec

    def get_by_id(
        self, identifier: str, db: Optional[Session] = None
    ) -> RecommendationResponse:
        rec = store.get_recommendation(identifier)
        if not rec and db:
            rec = recommendation_repo.get_by_id(db, identifier) or recommendation_repo.get_by_product_id(db, identifier)

        if not rec:
            raise AppException(
                code="REPORT_NOT_FOUND",
                message=f"No recommendation report found with ID '{identifier}'",
                field="identifier",
                status_code=404,
            )
        return rec


recommendation_service = RecommendationService()
