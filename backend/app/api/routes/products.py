"""
Product identification, registration, and catalog routes.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.knowledge.models_catalog import get_all_models
from app.schemas.product import (
    ProductCandidate,
    ProductCreate,
    ProductIdentifyRequest,
    ProductIdentifyResponse,
    ProductRecord,
)
from app.services.product_service import product_service
from app.services.vision import vision_service
from app.utils.uploads import validate_and_process_upload_files

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/identify", response_model=ProductIdentifyResponse)
async def identify_product(request: Request):
    """
    Identifies device model from uploaded images (1-3) or manual model selection.
    Thin route handler delegating directly to vision_service.
    """
    content_type = request.headers.get("content-type", "")
    if "multipart/form-data" in content_type:
        form = await request.form()
        raw_files = form.getlist("images") + form.getlist("files")
        uploaded_files = [f for f in raw_files if hasattr(f, "filename") and hasattr(f, "read")]
        hint = form.get("hint")
        manual_model = form.get("manual_model")
        model_id = form.get("model_id")

        image_bytes = None
        if uploaded_files:
            processed = await validate_and_process_upload_files(uploaded_files, min_files=1, max_files=3)
            image_bytes = [img.data for img in processed]

        return vision_service.identify(
            image_bytes_list=image_bytes,
            manual_model=str(manual_model) if manual_model else None,
            model_id=str(model_id) if model_id else None,
            hint=str(hint) if hint else None,
        )

    # JSON payload
    body = await request.json() if request.headers.get("content-length", "0") != "0" else {}
    req = ProductIdentifyRequest(**body)
    return vision_service.identify(
        image_bytes_list=None,
        manual_model=req.manual_model,
        model_id=req.model_id,
        hint=req.hint,
    )


@router.post("", response_model=ProductRecord)
def create_or_confirm_product(data: ProductCreate, db: Session = Depends(get_db)):
    return product_service.create_or_confirm(data, db=db)


@router.get("/catalog", response_model=List[ProductCandidate])
def get_supported_catalog():
    return get_all_models()


@router.get("/{product_id}", response_model=ProductRecord)
def get_product(product_id: str, db: Session = Depends(get_db)):
    return product_service.get_by_id(product_id, db=db)
