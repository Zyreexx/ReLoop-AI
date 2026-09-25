"""
User symptom parsing and classification routes.
"""
from fastapi import APIRouter
from app.schemas.symptoms import (
    SymptomInput,
    SymptomParseResult,
)
from app.services.symptom_service import symptom_service

router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


@router.post("/parse", response_model=SymptomParseResult)
def parse_symptoms(data: SymptomInput):
    return symptom_service.parse_and_record(data)
