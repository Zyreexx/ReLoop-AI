"""
Location-based discovery API routes for nearby electronics repair shops and certified recyclers.
"""
from typing import List, Optional
from fastapi import APIRouter, Query

from app.schemas.locator import CertificationStandardInfo, LocatorSearchResult
from app.services.locator_service import locator_service

router = APIRouter(prefix="/locator", tags=["Repair & Recycler Locator"])


@router.get("/search", response_model=LocatorSearchResult)
async def search_nearby_facilities(
    lat: Optional[float] = Query(None, description="GPS Latitude"),
    lon: Optional[float] = Query(None, description="GPS Longitude"),
    query: Optional[str] = Query(None, description="City, postal code, or address (e.g. 'Pune', 'Berlin', 'Austin')"),
    category: str = Query("ALL", description="Filter by facility type: 'ALL', 'REPAIR', 'RECYCLE'"),
    radius_km: float = Query(25.0, ge=1.0, le=100.0, description="Search radius in kilometers"),
):
    """
    Search for nearby electronics repair businesses and certified e-waste recyclers
    using OpenStreetMap geospatial data and R2v3 / e-Stewards certification directories.
    """
    return await locator_service.search_nearby(
        latitude=lat,
        longitude=lon,
        query=query,
        category=category.upper(),
        radius_km=radius_km,
    )


@router.get("/certifications", response_model=List[CertificationStandardInfo])
def get_certification_standards():
    """Retrieve accredited e-waste certification standards (SERI R2v3 and e-Stewards)."""
    return locator_service.get_certification_standards()

