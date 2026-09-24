"""
Curated knowledge base of supported demo laptop models and hardware specs.
Used as DATABASE evidence facts for compatibility and modularity.
"""
from typing import Dict, List, Optional
from app.schemas.enums import DeviceCategory, ConfidenceLevel
from app.schemas.product import ProductCandidate, ProductSpecs


CATALOG: Dict[str, dict] = {
    "dell-latitude-5420": {
        "slug": "dell-latitude-5420",
        "manufacturer": "Dell",
        "model": "Latitude 5420",
        "model_year": 2021,
        "category": DeviceCategory.LAPTOP,
        "specs": ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=True,
            ssd_modular=True,
            battery_replaceable=True,
            display_size_inches=14.0,
            weight_kg=1.40,
            baseline_embodied_co2_kg=295.0,
            estimated_original_msrp_usd=1200.0,
        ),
        "modularity_details": {
            "ram_slots": 2,
            "max_ram_gb": 64,
            "storage_slots": "1x M.2 NVMe 2280",
            "battery_screws": "4x Phillips #00 (non-glued)",
            "keyboard_serviceable": True,
            "thermal_serviceable": True,
        },
        "typical_costs_usd": {
            "battery_replacement": (45.0, 75.0),
            "ram_upgrade_16gb": (35.0, 55.0),
            "ssd_upgrade_1tb": (65.0, 95.0),
            "keyboard_replacement": (30.0, 50.0),
            "thermal_service": (15.0, 30.0),
            "screen_replacement": (80.0, 130.0),
        },
        "recovery_yield_pct": 82.0,
    },
    "lenovo-thinkpad-t490": {
        "slug": "lenovo-thinkpad-t490",
        "manufacturer": "Lenovo",
        "model": "ThinkPad T490",
        "model_year": 2019,
        "category": DeviceCategory.LAPTOP,
        "specs": ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=True,  # 1 soldered + 1 SO-DIMM
            ssd_modular=True,
            battery_replaceable=True,
            display_size_inches=14.0,
            weight_kg=1.46,
            baseline_embodied_co2_kg=310.0,
            estimated_original_msrp_usd=1350.0,
        ),
        "modularity_details": {
            "ram_slots": 1,  # 1 soldered + 1 slot
            "max_ram_gb": 40,
            "storage_slots": "1x M.2 NVMe",
            "battery_screws": "Captive screws (standard screwdriver)",
            "keyboard_serviceable": True,
            "thermal_serviceable": True,
        },
        "typical_costs_usd": {
            "battery_replacement": (50.0, 80.0),
            "ram_upgrade_16gb": (35.0, 55.0),
            "ssd_upgrade_1tb": (65.0, 95.0),
            "keyboard_replacement": (35.0, 60.0),
            "thermal_service": (15.0, 25.0),
            "screen_replacement": (90.0, 140.0),
        },
        "recovery_yield_pct": 85.0,
    },
    "macbook-pro-13-2019": {
        "slug": "macbook-pro-13-2019",
        "manufacturer": "Apple",
        "model": "MacBook Pro 13-inch (2019)",
        "model_year": 2019,
        "category": DeviceCategory.LAPTOP,
        "specs": ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=False,  # Soldered LPDDR3
            ssd_modular=False,  # Soldered NVMe
            battery_replaceable=False,  # Glued in chassis
            display_size_inches=13.3,
            weight_kg=1.37,
            baseline_embodied_co2_kg=270.0,
            estimated_original_msrp_usd=1299.0,
        ),
        "modularity_details": {
            "ram_slots": 0,
            "max_ram_gb": 16,
            "storage_slots": "Soldered on Logic Board",
            "battery_screws": "Glued battery cells (specialized solvent required)",
            "keyboard_serviceable": False,  # Riveted to top case
            "thermal_serviceable": True,
        },
        "typical_costs_usd": {
            "battery_replacement": (120.0, 199.0),
            "ram_upgrade_16gb": (0.0, 0.0),  # Not possible
            "ssd_upgrade_1tb": (0.0, 0.0),  # Not possible
            "keyboard_replacement": (180.0, 280.0),  # Requires whole top case
            "thermal_service": (25.0, 45.0),
            "screen_replacement": (220.0, 350.0),
        },
        "recovery_yield_pct": 65.0,
    },
    "hp-elitebook-840-g6": {
        "slug": "hp-elitebook-840-g6",
        "manufacturer": "HP",
        "model": "EliteBook 840 G6",
        "model_year": 2019,
        "category": DeviceCategory.LAPTOP,
        "specs": ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=True,
            ssd_modular=True,
            battery_replaceable=True,
            display_size_inches=14.0,
            weight_kg=1.48,
            baseline_embodied_co2_kg=290.0,
            estimated_original_msrp_usd=1250.0,
        ),
        "modularity_details": {
            "ram_slots": 2,
            "max_ram_gb": 64,
            "storage_slots": "1x M.2 PCIe NVMe",
            "battery_screws": "Modular latch / internal screws",
            "keyboard_serviceable": True,
            "thermal_serviceable": True,
        },
        "typical_costs_usd": {
            "battery_replacement": (45.0, 70.0),
            "ram_upgrade_16gb": (35.0, 55.0),
            "ssd_upgrade_1tb": (65.0, 95.0),
            "keyboard_replacement": (35.0, 55.0),
            "thermal_service": (15.0, 30.0),
            "screen_replacement": (85.0, 135.0),
        },
        "recovery_yield_pct": 80.0,
    },
    "asus-zenbook-ux425": {
        "slug": "asus-zenbook-ux425",
        "manufacturer": "ASUS",
        "model": "ZenBook UX425",
        "model_year": 2020,
        "category": DeviceCategory.LAPTOP,
        "specs": ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=False,  # Soldered LPDDR4X
            ssd_modular=True,   # M.2 NVMe SSD
            battery_replaceable=True,
            display_size_inches=14.0,
            weight_kg=1.17,
            baseline_embodied_co2_kg=260.0,
            estimated_original_msrp_usd=999.0,
        ),
        "modularity_details": {
            "ram_slots": 0,
            "max_ram_gb": 16,
            "storage_slots": "1x M.2 NVMe",
            "battery_screws": "Phillips screws",
            "keyboard_serviceable": False,
            "thermal_serviceable": True,
        },
        "typical_costs_usd": {
            "battery_replacement": (50.0, 80.0),
            "ram_upgrade_16gb": (0.0, 0.0),  # Not possible
            "ssd_upgrade_1tb": (65.0, 95.0),
            "keyboard_replacement": (120.0, 170.0),
            "thermal_service": (20.0, 35.0),
            "screen_replacement": (110.0, 160.0),
        },
        "recovery_yield_pct": 74.0,
    },
}


def lookup_model(query: str) -> Optional[dict]:
    q = query.strip().lower()
    for slug, data in CATALOG.items():
        if slug in q or q in slug:
            return data
        full_name = f"{data['manufacturer']} {data['model']}".lower()
        if full_name in q or q in full_name:
            return data
        # Check partial model matches
        if data["model"].lower() in q:
            return data
    return None


def get_all_models() -> List[ProductCandidate]:
    return [
        ProductCandidate(
            manufacturer=item["manufacturer"],
            model=item["model"],
            model_year=item["model_year"],
            confidence=ConfidenceLevel.HIGH,
            specs=item["specs"],
        )
        for item in CATALOG.values()
    ]
