"""
Hardware diagnostic input, validation, and agent session routes.
"""
import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.schemas.diagnostics import (
    DiagnosticsInput,
    DiagnosticValidationResult,
    DiagnosticSessionCreate,
    DiagnosticSessionResponse,
    DiagnosticSessionSubmit,
    DiagnosticSessionReport,
)
from app.services.diagnostic_service import diagnostic_service

router = APIRouter(prefix="/diagnostics", tags=["Diagnostics"])


@router.post("/validate", response_model=DiagnosticValidationResult)
def validate_diagnostics(data: DiagnosticsInput):
    """
    Validate manually entered or parsed hardware diagnostic metrics.
    """
    return diagnostic_service.validate_and_record(data)


@router.post("/session", response_model=DiagnosticSessionResponse)
def create_diagnostic_session(data: DiagnosticSessionCreate):
    """
    Generate a new diagnostic session token to bind local agent execution to this assessment.
    """
    return diagnostic_service.create_session(data.product_id)


@router.get("/session/{token}", response_model=DiagnosticSessionReport)
def get_diagnostic_session_report(token: str):
    """
    Retrieve completed diagnostic report and findings for a session.
    """
    session = diagnostic_service.get_session(token)
    if not session:
        raise HTTPException(status_code=404, detail=f"Diagnostic session '{token}' not found.")
    report = session.get("report")
    if not report:
        return DiagnosticSessionReport(
            session_token=token,
            product_id=session.get("product_id"),
            status=session.get("status", "PENDING"),
            overall_hardware_health="UNKNOWN",
            subsystems={},
            faults=[],
            summary={},
            evidence_items=[],
            ai_explanation=None,
        )
    return report


@router.get("/session/{token}/status")
def get_diagnostic_session_status(token: str):
    """
    Poll live subsystem progress and completion status for a running session.
    """
    session = diagnostic_service.get_session(token)
    if not session:
        raise HTTPException(status_code=404, detail=f"Diagnostic session '{token}' not found.")
    return {
        "session_token": token,
        "product_id": session.get("product_id"),
        "status": session.get("status", "PENDING"),
        "subsystems_progress": session.get("subsystems_progress", {}),
        "report": session.get("report"),
    }


@router.post("/session/{token}/submit", response_model=DiagnosticSessionReport)
def submit_diagnostic_session(token: str, data: DiagnosticSessionSubmit):
    """
    Endpoint called by local diagnostic agent to deliver collected hardware telemetry.
    """
    return diagnostic_service.submit_session(token, data)


@router.get("/agent/download")
def download_diagnostic_agent():
    """
    Serve the standalone reloop_agent.py diagnostic script.
    """
    # Search candidates across backend, frontend public, and project root
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../reloop_agent.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../frontend/public/reloop_agent.py")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../backend/reloop_agent.py")),
        os.path.abspath("backend/reloop_agent.py"),
        os.path.abspath("reloop_agent.py"),
    ]
    agent_path = next((p for p in candidates if os.path.exists(p)), None)
    if not agent_path:
        raise HTTPException(status_code=404, detail="reloop_agent.py script not found on server.")
    return FileResponse(
        agent_path,
        media_type="text/x-python",
        filename="reloop_agent.py",
    )
