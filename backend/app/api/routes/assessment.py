"""
Assessment and condition profile synthesis routes.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.db.store import store
from app.schemas.condition import ConditionProfile
from app.schemas.errors import AppException
from app.services.assessment_service import assessment_service

router = APIRouter(prefix="/assessment", tags=["Assessment"])


class BuildAssessmentRequest(BaseModel):
    product_id: str


@router.post("/build", response_model=ConditionProfile)
def build_assessment(req: BuildAssessmentRequest):
    return assessment_service.build_profile(req.product_id)


@router.get("/{product_id}", response_model=ConditionProfile)
def get_assessment_profile(product_id: str):
    profile = store.get_profile(product_id)
    if not profile:
        # Build if not already built
        return assessment_service.build_profile(product_id)
    return profile
