"""
Digital Product Passport (DPP) API routes conforming to EU ESPR & CIRPASS specifications.
"""
import base64
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dpp import DigitalProductPassport
from app.services.dpp_service import dpp_service

router = APIRouter(prefix="/dpp", tags=["Digital Product Passport"])


@router.post("/{product_id}/generate", response_model=DigitalProductPassport)
def generate_product_passport(
    product_id: str,
    db: Session = Depends(get_db),
):
    """
    Generate an authentic, cryptographic Digital Product Passport (DPP) for a registered device,
    calculating EU repairability indexes, material declarations, and QR codes.
    """
    try:
        return dpp_service.generate_passport(product_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate DPP: {str(e)}")


@router.get("/{dpp_id}", response_model=DigitalProductPassport)
def get_product_passport(dpp_id: str):
    """Retrieve public passport details by DPP URN identifier with privacy safeguards."""
    passport = dpp_service.get_public_passport(dpp_id)
    if not passport:
        raise HTTPException(status_code=404, detail=f"Digital Product Passport '{dpp_id}' not found")
    return passport


@router.get("/{dpp_id}/qr")
def get_passport_qr_code(dpp_id: str):
    """Retrieve the direct PNG image binary of the device's Digital Product Passport QR code."""
    passport = dpp_service.get_passport(dpp_id)
    if not passport or not passport.qr_code_base64:
        raise HTTPException(status_code=404, detail="Passport or QR code not found")

    # Extract raw base64 data from data URI
    header, encoded = passport.qr_code_base64.split(",", 1)
    png_bytes = base64.b64decode(encoded)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/{dpp_id}/export")
def export_cirpass_json(dpp_id: str):
    """Export standardized CIRPASS / ESPR compliant JSON document."""
    passport = dpp_service.get_passport(dpp_id)
    if not passport:
        raise HTTPException(status_code=404, detail="Passport not found")
    return Response(
        content=passport.model_dump_json(indent=2),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=dpp_{dpp_id.split(':')[-1]}.json"},
    )

