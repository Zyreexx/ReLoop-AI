"""
Pytest configuration and shared test fixtures.
"""
import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.main import app
from app.db.store import store
from app.schemas.product import ProductRecord, ProductSpecs
from app.schemas.enums import DeviceCategory, ComponentStatus, ConfidenceLevel, EvidenceType
from app.schemas.evidence import EvidenceItem
from app.schemas.condition import ComponentCondition, ConditionProfile


@pytest.fixture(autouse=True)
def clean_store():
    """Reset in-memory store before each test run."""
    store.clear()
    yield
    store.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def dell_latitude_5420():
    return ProductRecord(
        id="prod_test_dell",
        manufacturer="Dell",
        model="Latitude 5420",
        model_year=2021,
        category=DeviceCategory.LAPTOP,
        age_years=4.5,
        specs=ProductSpecs(
            category=DeviceCategory.LAPTOP,
            ram_modular=True,
            ssd_modular=True,
            battery_replaceable=True,
            weight_kg=1.40,
            baseline_embodied_co2_kg=295.0,
            estimated_original_msrp_usd=1200.0,
        ),
    )


@pytest.fixture
def repairable_condition_profile(dell_latitude_5420):
    """The canonical demo device from memory.md:
    - Weak battery (73%)
    - Minor keyboard damage (missing key)
    - Healthy SSD (91%)
    - Passing RAM test
    - Thermal throttling (service required)
    """
    profile = ConditionProfile(
        product_id=dell_latitude_5420.id,
        overall_hardware_health="FAIR",
        components={
            "battery": ComponentCondition(
                component="battery",
                status=ComponentStatus.SERVICE_REQUIRED,
                label="73% — Service Recommended",
                observations=["Full charge capacity 42,340 mWh of 58,000 mWh design."],
                measurements={"health_percentage": "73.0%", "cycle_count": "584"},
                evidence_ids=["ev_batt_1"],
                evidence_sources=["OS Battery Diagnostic Report"],
                repairable=True,
            ),
            "ssd": ComponentCondition(
                component="ssd",
                status=ComponentStatus.GOOD,
                label="91% — Healthy",
                observations=["SMART health 91%; 0 media errors."],
                measurements={"health_percentage": "91.0%", "smart_status": "PASS"},
                evidence_ids=["ev_ssd_1"],
                evidence_sources=["Storage Controller SMART Diagnostic"],
                repairable=True,
                upgradeable=True,
            ),
            "ram": ComponentCondition(
                component="ram",
                status=ComponentStatus.GOOD,
                label="PASS",
                observations=["16GB DDR4 SO-DIMM passed memory diagnostic."],
                measurements={"diagnostic_result": "PASS", "capacity_gb": "16 GB"},
                evidence_ids=["ev_ram_1"],
                evidence_sources=["UEFI MemTest"],
                repairable=True,
                upgradeable=True,
            ),
            "thermals": ComponentCondition(
                component="thermals",
                status=ComponentStatus.SERVICE_REQUIRED,
                label="Service Required",
                observations=["Peak temperature 96°C under workload; thermal throttling flagged."],
                measurements={"cpu_max_temp": "96°C"},
                evidence_ids=["ev_thm_1"],
                evidence_sources=["Thermal Monitoring Log / HWInfo"],
                repairable=True,
            ),
            "display": ComponentCondition(
                component="display",
                status=ComponentStatus.GOOD,
                label="Clean / No Cracks",
                observations=["Display glass intact, no pixel defects."],
                evidence_ids=["ev_disp_1"],
                evidence_sources=["Optical Inspection"],
                repairable=True,
            ),
            "keyboard": ComponentCondition(
                component="keyboard",
                status=ComponentStatus.SERVICE_REQUIRED,
                label="Key Damage / Missing",
                observations=["Missing keycap on keyboard deck."],
                evidence_ids=["ev_kb_1"],
                evidence_sources=["Optical Inspection"],
                repairable=True,
            ),
            "chassis": ComponentCondition(
                component="chassis",
                status=ComponentStatus.FAIR,
                label="Moderate Cosmetic Wear",
                observations=["Light scuffs; hinges firm."],
                evidence_ids=["ev_chas_1"],
                evidence_sources=["Optical Inspection"],
                repairable=True,
            ),
            "system": ComponentCondition(
                component="system",
                status=ComponentStatus.GOOD,
                label="POST & Power OK",
                observations=["Motherboard power circuitry operating normally."],
                evidence_ids=["ev_sys_1"],
                evidence_sources=["Diagnostic Check"],
                repairable=False,
            ),
        },
    )
    store.save_product(dell_latitude_5420)
    store.save_profile(profile)
    return profile
