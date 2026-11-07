"""
Digital Product Passport (DPP) Schemas conforming to European ESPR
(Ecodesign for Sustainable Products Regulation) and CIRPASS guidelines.
"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class DPPProductIdentification(BaseModel):
    gtin_or_ean: Optional[str] = None
    serial_or_identifier: Optional[str] = None
    manufacturer: str
    model: str
    category: str = "Laptop / Portable Computer"
    model_year: int
    country_of_origin: Optional[str] = None


class DPPSustainabilityMaterials(BaseModel):
    embodied_co2_kg: float = 280.0
    recycled_content_percent: float = 25.0
    critical_raw_materials_declared: List[str] = Field(
        default_factory=lambda: ["Cobalt (Battery)", "Lithium (Battery)", "Rare Earth Elements (Neodymium Magnets)", "Gold (PCB Traces)"]
    )
    rohs_reach_compliant: bool = True
    battery_chemistry: str = "Lithium-Ion / Li-Polymer"
    hazardous_substances_declaration: str = "Compliant with EU RoHS Directive 2011/65/EU and REACH Regulation (EC) 1907/2006."


class DPPRepairabilityCircularity(BaseModel):
    repairability_score: float = Field(..., ge=0.0, le=10.0, description="EU / French Repairability Index (0.0 to 10.0)")
    modularity_rating: str = Field("HIGH", description="HIGH, MODERATE, LOW, PROPRIETARY")
    battery_replaceable: bool = True
    ram_modular: bool = True
    storage_modular: bool = True
    fasteners_type: str = "Standard Torx T5 / Phillips #00 (Non-Proprietary)"
    disassembly_manual_url: Optional[str] = None
    spare_parts_availability_years: int = 7


class DPPComponentHealth(BaseModel):
    component: str
    status: str
    provenance_source: str
    confidence: str
    observations: List[str] = Field(default_factory=list)
    measurements: Dict[str, str] = Field(default_factory=dict)


class DPPLifecycleEvent(BaseModel):
    event_id: str
    event_type: str  # "MANUFACTURING", "ASSESSMENT", "REPAIR", "UPGRADE", "REFURBISHMENT"
    timestamp: str
    organization: str
    details: str
    verification_hash: Optional[str] = None


class DPPEndOfLifeGuidance(BaseModel):
    dismantling_difficulty: str = "LOW"
    battery_removal_required_before_shredding: bool = True
    recommended_recycler_certification: str = "R2v3 or e-Stewards Certified Recycler"
    circular_disposition: str = "Component Recovery (Harvest modular RAM/SSD/Display before smelting)"
    e_waste_category: str = "WEEE Category 3 (IT and Telecommunications Equipment)"


class DigitalProductPassport(BaseModel):
    dpp_id: str
    schema_version: str = "CIRPASS-ESPR-v1.0"
    issue_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    valid_until: Optional[str] = None
    verification_status: str = "VERIFIED"  # "VERIFIED", "PENDING_AUDIT", "COMMUNITY_REPORTED"
    verification_hash: str  # SHA-256 cryptographic proof
    product_identification: DPPProductIdentification
    sustainability_and_materials: DPPSustainabilityMaterials
    repairability_and_circularity: DPPRepairabilityCircularity
    component_health_provenance: List[DPPComponentHealth] = Field(default_factory=list)
    lifecycle_history: List[DPPLifecycleEvent] = Field(default_factory=list)
    end_of_life_guidance: DPPEndOfLifeGuidance
    public_url: str
    qr_code_base64: Optional[str] = None

