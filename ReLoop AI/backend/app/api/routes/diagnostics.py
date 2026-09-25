"""
Hardware diagnostic input and validation routes.
"""
from fastapi import APIRouter
from app.schemas.diagnostics import (
    DiagnosticsInput,
    DiagnosticValidationResult,
)
from app.services.diagnostic_service import diagnostic_service

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.post("/validate", response_model=DiagnosticValidationResult)
def validate_diagnostics(data: DiagnosticsInput):
    return diagnostic_service.validate_and_record(data)
