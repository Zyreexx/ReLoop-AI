"""
Curated knowledge base of supported demo laptop models and hardware specs.
Used as DATABASE evidence facts for compatibility and modularity.
Backed by structured JSON definitions in data/products/.
"""
from typing import Dict, List, Optional
from app.knowledge.loader import (
    load_all_products,
    get_model_spec,
    get_supported_product_candidates,
    get_supported_models,
)
from app.schemas.enums import DeviceCategory, ConfidenceLevel
from app.schemas.product import ProductCandidate, ProductSpecs


def _get_catalog_dict() -> Dict[str, dict]:
    raw_products = load_all_products()
    catalog: Dict[str, dict] = {}
    for slug, item in raw_products.items():
        specs_data = item.get("specs", {})
        if isinstance(specs_data, dict):
            specs = ProductSpecs(**specs_data)
        elif isinstance(specs_data, ProductSpecs):
            specs = specs_data
        else:
            specs = ProductSpecs()

        catalog[slug] = {
            "slug": slug,
            "manufacturer": item.get("manufacturer", "Generic"),
            "model": item.get("model", "Laptop"),
            "model_year": item.get("model_year", 2020),
            "category": DeviceCategory.LAPTOP,
            "specs": specs,
            "modularity_details": item.get("component_configuration", {}),
            "typical_costs_inr": item.get("typical_repair_cost_inr", {}),
            "repairability_score": item.get("repairability_score", {}),
            "recovery_yield_pct": 80.0,
            "raw_data": item,
        }
    return catalog


# Dynamic proxy or populated catalog
CATALOG: Dict[str, dict] = _get_catalog_dict()


def lookup_model(query: str) -> Optional[dict]:
    """
    Searches for a model matching the query string.
    Returns the catalog dictionary or None.
    """
    if not query:
        return None
    try:
        raw_spec = get_model_spec(query)
        slug = raw_spec.get("slug", query.lower().replace(" ", "-"))
        specs_data = raw_spec.get("specs", {})
        if isinstance(specs_data, dict):
            specs = ProductSpecs(**specs_data)
        elif isinstance(specs_data, ProductSpecs):
            specs = specs_data
        else:
            specs = ProductSpecs()

        return {
            "slug": slug,
            "manufacturer": raw_spec.get("manufacturer", "Generic"),
            "model": raw_spec.get("model", "Laptop"),
            "model_year": raw_spec.get("model_year", 2020),
            "category": DeviceCategory.LAPTOP,
            "specs": specs,
            "modularity_details": raw_spec.get("component_configuration", {}),
            "typical_costs_inr": raw_spec.get("typical_repair_cost_inr", {}),
            "repairability_score": raw_spec.get("repairability_score", {}),
            "recovery_yield_pct": 80.0,
            "raw_data": raw_spec,
        }
    except Exception:
        # Fallback to local catalog keys if any
        q = query.strip().lower()
        for slug, data in _get_catalog_dict().items():
            if slug in q or q in slug:
                return data
            full_name = f"{data['manufacturer']} {data['model']}".lower()
            if full_name in q or q in full_name:
                return data
            if data["model"].lower() in q:
                return data
        return None


def get_all_models() -> List[ProductCandidate]:
    """
    Returns all supported models as ProductCandidate list.
    """
    return get_supported_product_candidates()


def get_catalog_candidates_with_ids() -> List[dict]:
    """
    Returns the supported-model catalog sorted deterministically,
    with stable candidate IDs (C1, C2, C3, ...) generated from the sorted list.
    """
    raw_products = load_all_products()
    sorted_items = sorted(
        raw_products.values(),
        key=lambda item: (
            item.get("manufacturer", "").strip().lower(),
            item.get("model", "").strip().lower(),
            item.get("slug", "").strip().lower(),
        ),
    )
    candidates_with_ids = []
    for idx, item in enumerate(sorted_items, start=1):
        cid = f"C{idx}"
        specs_data = item.get("specs", {})
        specs = ProductSpecs(**specs_data) if isinstance(specs_data, dict) else ProductSpecs()
        candidate = ProductCandidate(
            manufacturer=item.get("manufacturer", "Generic"),
            model=item.get("model", "Laptop"),
            model_year=item.get("model_year", 2020),
            confidence=ConfidenceLevel.HIGH,
            specs=specs,
        )
        candidates_with_ids.append({
            "candidate_id": cid,
            "candidate": candidate,
            "raw_data": item,
            "slug": item.get("slug", ""),
            "manufacturer": item.get("manufacturer", "Generic"),
            "model": item.get("model", "Laptop"),
            "model_year": item.get("model_year", 2020),
            "specs": specs,
        })
    return candidates_with_ids


def get_candidate_by_id(candidate_id: str) -> Optional[dict]:
    """
    Look up a catalog candidate item by its stable candidate ID (e.g. 'C1', 'C2').
    """
    if not candidate_id or candidate_id.strip().upper() == "UNKNOWN":
        return None
    clean_id = candidate_id.strip().upper()
    candidates = get_catalog_candidates_with_ids()
    for item in candidates:
        if item["candidate_id"].upper() == clean_id:
            return item
    # Also support prefix matching like 'C2: Dell Latitude' -> 'C2'
    if clean_id.startswith("C") and len(clean_id) > 1:
        first_token = clean_id.split()[0].split(":")[0].split("-")[0].strip()
        for item in candidates:
            if item["candidate_id"].upper() == first_token:
                return item
    return None


def format_candidates_for_prompt() -> str:
    """
    Formats the stable candidate list for injection into Gemini prompt:
    - C1: Apple MacBook Air (M1, 2020) (2020)
    - C2: Dell Latitude 5420 (2021)
    ...
    """
    lines = []
    for c in get_catalog_candidates_with_ids():
        lines.append(f"- {c['candidate_id']}: {c['manufacturer']} {c['model']} ({c['model_year']})")
    return "\n".join(lines)
