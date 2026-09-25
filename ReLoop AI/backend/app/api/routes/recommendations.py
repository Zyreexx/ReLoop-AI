"""
Recommendation generation and condition report retrieval routes.
"""
from fastapi import APIRouter
from app.schemas.recommendation import (
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_service import recommendation_service

router = APIRouter(tags=["Recommendations & Reports"])


@router.post("/recommendations/generate", response_model=RecommendationResponse)
def generate_recommendation(req: RecommendationRequest):
    return recommendation_service.generate_recommendation(req)


@router.get("/reports/{identifier}", response_model=RecommendationResponse)
def get_recommendation_report(identifier: str):
    return recommendation_service.get_by_id(identifier)
