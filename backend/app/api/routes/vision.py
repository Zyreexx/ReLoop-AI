"""
Optical inspection and visible damage analysis routes.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.errors import AppError, ErrorCode
from app.schemas.vision import VisionAnalyzeRequest, VisionAnalyzeResponse
from app.services.vision import vision_service
from app.utils.uploads import validate_and_process_upload_files

router = APIRouter(prefix="/vision", tags=["Vision"])


@router.post("/analyze", response_model=VisionAnalyzeResponse)
async def analyze_visible_damage(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Analyzes visible damage from optical inspection photos (1-3) or inspection notes.
    Saves results as VISUAL Evidence records linked to the product.
    Thin route handler delegating directly to vision_service.
    """
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        product_id = form.get("product_id")
        if not product_id:
            raise AppError(
                code=ErrorCode.INVALID_INPUT.value,
                message="product_id is required.",
                field="product_id",
                http_status=400,
            )

        inspection_notes = form.get("inspection_notes")
        raw_files = form.getlist("images") + form.getlist("files")
        uploaded_files = [f for f in raw_files if hasattr(f, "filename") and hasattr(f, "read")]

        image_bytes = None
        image_names = None
        if uploaded_files:
            processed = await validate_and_process_upload_files(uploaded_files, min_files=1, max_files=6)
            image_bytes = [img.data for img in processed]
            image_names = [img.filename for img in processed]

        return vision_service.analyze(
            product_id=str(product_id),
            image_bytes_list=image_bytes,
            inspection_notes=str(inspection_notes) if inspection_notes else None,
            image_names=image_names,
            db=db,
        )

    # JSON payload
    body = await request.json()
    req = VisionAnalyzeRequest(**body)
    return vision_service.analyze(
        product_id=req.product_id,
        image_bytes_list=None,
        inspection_notes=req.inspection_notes,
        image_names=req.image_names,
        db=db,
    )

