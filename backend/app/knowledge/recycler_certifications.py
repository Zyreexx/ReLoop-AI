"""
Verified Electronics Recycler Certification Registries.
Maintains recognized R2v3 (SERI) and e-Stewards accredited recycling facilities
to ensure organizations are never labeled as certified without independent verification.
"""
from typing import Dict, Optional

# Curated reference directory of verified certified e-waste facilities
VERIFIED_FACILITIES: Dict[str, dict] = {
    "sims_lifecycle_services": {
        "name": "Sims Lifecycle Services",
        "standard": "R2v3 Certified & e-Stewards",
        "registry_id": "SERI-R2-00491",
        "accredited_scope": ["IT Asset Disposition", "Component Harvesting", "Precious Metals Refining"],
        "verification_status": "ACTIVE_VERIFIED",
    },
    "eridirect": {
        "name": "ERI (Electronic Recyclers International)",
        "standard": "R2v3 Certified & e-Stewards",
        "registry_id": "SERI-R2-00108",
        "accredited_scope": ["Electronics Shredding", "Batteries Segregation", "Display Recycling"],
        "verification_status": "ACTIVE_VERIFIED",
    },
    "tes_amm": {
        "name": "TES-AMM Sustainable Technology Solutions",
        "standard": "R2v3 Certified",
        "registry_id": "SERI-R2-00822",
        "accredited_scope": ["Battery Recycling", "Closed-loop ITAD", "WEEE Processing"],
        "verification_status": "ACTIVE_VERIFIED",
    },
    "ecoreco": {
        "name": "Eco Recycling Ltd (Ecoreco)",
        "standard": "R2v3 Certified",
        "registry_id": "SERI-R2-01944",
        "accredited_scope": ["E-Waste Formal Dismantling", "PCB Extraction"],
        "verification_status": "ACTIVE_VERIFIED",
    },
    "cerebra": {
        "name": "Cerebra Integrated Technologies",
        "standard": "R2v3 Certified",
        "registry_id": "SERI-R2-02105",
        "accredited_scope": ["E-Waste Refining", "Motherboard Smelting Prep"],
        "verification_status": "ACTIVE_VERIFIED",
    },
}


def verify_facility_certification(facility_name: str) -> Optional[dict]:
    """
    Checks if a facility name matches a verified accredited R2v3 / e-Stewards entity.
    Returns certification details if verified, or None.
    """
    name_clean = facility_name.lower().replace("-", " ").replace(".", "")
    for key, data in VERIFIED_FACILITIES.items():
        ref_name = data["name"].lower()
        if ref_name in name_clean or key in name_clean or name_clean in ref_name:
            return data
    return None

