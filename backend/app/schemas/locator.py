"""
Schemas for Location-Based Repair Shop & Certified E-Waste Recycler Discovery.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class LocatorItem(BaseModel):
    id: str
    name: str
    category: str = Field(..., description="REPAIR_SHOP, CERTIFIED_RECYCLER, or E_WASTE_COLLECTOR")
    address: str
    city: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    opening_hours: Optional[str] = None
    latitude: float
    longitude: float
    distance_km: float
    is_certified: bool = False
    certification_badge: Optional[str] = None  # "R2v3 Certified", "e-Stewards Certified", None
    accepted_items: List[str] = Field(default_factory=lambda: ["Laptops", "Desktops", "Batteries", "Monitors"])
    directions_url: str


class LocatorSearchResult(BaseModel):
    query_location: str
    latitude: float
    longitude: float
    radius_km: float
    total_results: int
    repair_shops_count: int
    recyclers_count: int
    results: List[LocatorItem] = Field(default_factory=list)


class CertificationStandardInfo(BaseModel):
    standard_name: str
    governing_body: str
    description: str
    verification_method: str
    official_registry_url: str

