"""
Product identification, registration, and catalog routes.
"""
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.knowledge.models_catalog import get_all_models
from app.schemas.product import (
    ProductCandidate,
    ProductCreate,
    ProductIdentificationRequest,
    ProductIdentificationResponse,
    ProductRecord,
)
from app.services.product_service import product_service

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/identify", response_model=ProductIdentificationResponse)
def identify_product(req: ProductIdentificationRequest):
    return product_service.identify(req)


@router.post("", response_model=ProductRecord)
def create_or_confirm_product(data: ProductCreate, db: Session = Depends(get_db)):
    return product_service.create_or_confirm(data, db=db)


@router.get("/catalog", response_model=List[ProductCandidate])
def get_supported_catalog():
    return get_all_models()


@router.get("/{product_id}", response_model=ProductRecord)
def get_product(product_id: str, db: Session = Depends(get_db)):
    return product_service.get_by_id(product_id, db=db)
