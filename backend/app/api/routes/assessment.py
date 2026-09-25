"""
Assessment and condition profile synthesis routes.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.store import store
from app.schemas.condition import ConditionProfile
from app.schemas.errors import AppException
from app.services.assessment_service import assessment_service

router = APIRouter(prefix="/assessment", tags=["Assessment"])


class BuildAssessmentRequest(BaseModel):
    product_id: str


@router.post("/build", response_model=ConditionProfile)
def build_assessment(
    req: BuildAssessmentRequest,
    db: Session = Depends(get_db),
):
    """
    Synthesizes component-level condition profile from evidence provenance.
    Idempotent: Resubmitting the same assessment overwrites/updates the existing assessment.
    """
    return assessment_service.build_profile(req.product_id, db=db)


@router.get("/{product_id}", response_model=ConditionProfile)
def get_assessment_profile(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves the synthesized condition profile for a product.
    """
    from app.db.repositories import assessment_repo
    profile = store.get_profile(product_id)
    if not profile and db:
        profile = assessment_repo.get_by_product_id(db, product_id)
    if not profile:
        # Build if not already built
        return assessment_service.build_profile(product_id, db=db)
    return profile
