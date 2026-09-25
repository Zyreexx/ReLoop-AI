"""
Recommendation generation routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import recommendation_service

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/generate", response_model=RecommendationResponse)
def generate_recommendation(
    req: RecommendationRequest,
    db: Session = Depends(get_db),
):
    """
    Executes the deterministic circular path optimizer for the given product and objective.
    Returns ranked pathways, score breakdown, evidence links, and assumptions.
    """
    return recommendation_service.generate_recommendation(req, db=db)
