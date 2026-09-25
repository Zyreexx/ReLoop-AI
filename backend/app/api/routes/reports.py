"""
Condition report and downloadable export routes.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.report import ConditionReportResponse
from app.services.report_service import report_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/{assessment_id}", response_model=ConditionReportResponse)
def get_condition_report(
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieves the complete condition report combining product, condition profile,
    recommendations, alternatives, impact estimates, assumptions, and data gaps.
    """
    return report_service.get_report(assessment_id, db=db)


@router.get("/{assessment_id}/download")
def download_condition_report(
    assessment_id: str,
    db: Session = Depends(get_db),
):
    """
    Exports the complete condition report as a downloadable JSON file.
    """
    report = report_service.get_report(assessment_id, db=db)
    json_content = report.model_dump_json(indent=2)
    return Response(
        content=json_content,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="reloop_report_{assessment_id}.json"',
        },
    )
