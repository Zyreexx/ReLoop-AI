"""
Structured knowledge loader for supported laptop models, specifications,
repair costs, and lifecycle assumptions.
Reads product definitions directly from data/products/*.json.
"""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from app.errors import AppError, ErrorCode, UNSUPPORTED_MODEL
from app.schemas.enums import ConfidenceLevel, DeviceCategory
from app.schemas.product import ProductCandidate, ProductSpecs

logger = logging.getLogger(__name__)


def get_products_data_dir() -> Path:
    """
    Resolves data/products directory across different execution contexts
    (repo root, backend subdir, tests, or Docker container).
    """
    candidates = [
        Path(__file__).resolve().parents[3] / "data" / "products",
        Path.cwd() / "data" / "products",
        Path.cwd().parent / "data" / "products",
        Path(__file__).resolve().parents[2] / "data" / "products",
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    # Default fallback
    return candidates[0]


def get_demo_data_dir() -> Path:
    """
    Resolves data/demo directory across execution contexts.
    """
    candidates = [
        Path(__file__).resolve().parents[3] / "data" / "demo",
        Path.cwd() / "data" / "demo",
        Path.cwd().parent / "data" / "demo",
        Path(__file__).resolve().parents[2] / "data" / "demo",
        Path(__file__).resolve().parents[2] / "tests" / "golden",
        Path.cwd() / "tests" / "golden",
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    return candidates[0]


_PRODUCTS_CACHE: Optional[Dict[str, dict]] = None


_GENERIC_CACHE: Optional[Dict[str, dict]] = None


def get_generic_laptop_profile(force_reload: bool = False) -> dict:
    """
    Loads the generic category-level laptop profile from data/products/_generic_laptop.json.
    """
    global _GENERIC_CACHE
    if _GENERIC_CACHE is not None and not force_reload:
        return _GENERIC_CACHE

    products_dir = get_products_data_dir()
    generic_file = products_dir / "_generic_laptop.json"
    if generic_file.exists():
        try:
            with open(generic_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                _GENERIC_CACHE = data
                return _GENERIC_CACHE
        except Exception as e:
            logger.error(f"Error loading generic product file {generic_file}: {e}")

    # Fallback in-memory default
    _GENERIC_CACHE = {
        "manufacturer": "Generic",
        "model": "General Laptop",
        "slug": "generic-laptop",
        "category": "LAPTOP",
        "is_generic": True,
        "specs": {
            "category": "LAPTOP",
            "ram_modular": True,
            "ssd_modular": True,
            "battery_replaceable": True,
            "display_size_inches": 14.0,
            "weight_kg": 1.50,
            "baseline_embodied_co2_kg": 280.0,
            "estimated_original_msrp_usd": 1000.0,
        },
        "repairability_score": {
            "score": 6.5,
            "max_score": 10.0,
            "basis": "GENERIC_CATEGORY_ESTIMATE",
            "note": "Broad category estimate: Standard notebook architecture with modular storage and memory.",
        },
        "typical_repair_cost_inr": {
            "battery": {"min": 2500, "max": 5000, "basis": "GENERIC_CATEGORY_ESTIMATE", "note": "Broad category estimate for replacement laptop battery."},
            "ssd": {"min": 2500, "max": 6000, "basis": "GENERIC_CATEGORY_ESTIMATE", "note": "Broad category estimate for standard M.2 NVMe SSD."},
            "ram": {"min": 1800, "max": 4000, "basis": "GENERIC_CATEGORY_ESTIMATE", "note": "Broad category estimate for standard SO-DIMM RAM."},
            "keyboard": {"min": 2000, "max": 4000, "basis": "GENERIC_CATEGORY_ESTIMATE", "note": "Broad category estimate for replacement laptop keyboard."},
            "thermals": {"min": 800, "max": 2000, "basis": "GENERIC_CATEGORY_ESTIMATE", "note": "Broad category estimate for thermal service and fan cleaning."},
            "display": {"min": 4000, "max": 8000, "basis": "GENERIC_CATEGORY_ESTIMATE", "note": "Broad category estimate for replacement laptop display panel."},
            "motherboard": {"min": 8000, "max": 18000, "basis": "GENERIC_CATEGORY_ESTIMATE", "note": "Broad category estimate for refurbished system board."},
        },
        "expected_useful_life": {
            "baseline_years": 5.0,
            "extended_years_post_repair": 2.5,
            "basis": "GENERIC_CATEGORY_ESTIMATE",
            "note": "Broad category estimate: Standard commercial notebook useful life baseline.",
        },
    }
    return _GENERIC_CACHE


def load_all_products(force_reload: bool = False) -> Dict[str, dict]:
    """
    Loads all non-generic product JSON files into an in-memory dictionary keyed by slug.
    Files starting with '_' (e.g. _generic_laptop.json) are excluded from the specific catalog.
    """
    global _PRODUCTS_CACHE
    if _PRODUCTS_CACHE is not None and not force_reload:
        return _PRODUCTS_CACHE

    products_dir = get_products_data_dir()
    cache: Dict[str, dict] = {}

    if products_dir.exists():
        for json_file in products_dir.glob("*.json"):
            if json_file.name.startswith("_"):
                continue
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    slug = data.get("slug") or json_file.stem.replace("_", "-")
                    data["slug"] = slug
                    cache[slug] = data
            except Exception as e:
                logger.error(f"Error loading product file {json_file}: {e}")

    _PRODUCTS_CACHE = cache
    return _PRODUCTS_CACHE


def get_supported_models() -> List[dict]:
    """
    Returns the list of all supported product model dictionaries.
    """
    cache = load_all_products()
    return list(cache.values())


def get_supported_product_candidates() -> List[ProductCandidate]:
    """
    Returns supported models formatted as ProductCandidate schemas.
    """
    models = get_supported_models()
    candidates: List[ProductCandidate] = []
    for item in models:
        specs_data = item.get("specs", {})
        if isinstance(specs_data, dict):
            specs = ProductSpecs(**specs_data)
        else:
            specs = ProductSpecs()

        candidates.append(
            ProductCandidate(
                manufacturer=item["manufacturer"],
                model=item["model"],
                model_year=item.get("model_year", 2020),
                confidence=ConfidenceLevel.HIGH,
                specs=specs,
            )
        )
    return candidates


def _normalize_string(s: str) -> str:
    return "".join(c.lower() for c in s if c.isalnum())


def match_catalog_model(manufacturer: Optional[str], model: Optional[str]) -> Optional[dict]:
    """
    Matches an identified manufacturer + model string to a catalog entry.
    - Case-insensitive match on manufacturer.
    - Fuzzy / normalized comparison of the model string against catalog entry's model,
      slug, and aliases.
    - If no match found -> returns None (does not guess a closest match).
    """
    if not manufacturer or not model:
        return None

    mfr_clean = manufacturer.strip().lower()
    model_clean = model.strip().lower()
    if mfr_clean in ["unknown", "generic"] or model_clean in ["unknown", "generic", "general laptop"]:
        return None

    products = load_all_products()
    model_norm = _normalize_string(model_clean)
    full_query_norm = _normalize_string(f"{mfr_clean} {model_clean}")

    # 1. Filter candidates by manufacturer
    mfr_matches = [
        p for p in products.values()
        if p.get("manufacturer", "").strip().lower() == mfr_clean
    ]
    if not mfr_matches:
        # Also check if manufacturer is Apple and model mentions MacBook, etc.
        mfr_matches = [
            p for p in products.values()
            if mfr_clean in p.get("manufacturer", "").strip().lower()
            or p.get("manufacturer", "").strip().lower() in mfr_clean
        ]
    if not mfr_matches:
        return None

    import re

    for prod in mfr_matches:
        prod_model = prod.get("model", "").strip().lower()
        prod_slug = prod.get("slug", "").strip().lower()
        prod_aliases = [str(a).strip().lower() for a in prod.get("aliases", []) if a]

        # Exact model string match
        if model_clean == prod_model or model_norm == _normalize_string(prod_model):
            return prod

        # Exact slug match
        if model_clean == prod_slug or model_norm == _normalize_string(prod_slug):
            return prod

        # Check full manufacturer + model normalized match
        prod_full_norm = _normalize_string(f"{prod.get('manufacturer', '')} {prod_model}")
        if model_norm == prod_full_norm or full_query_norm == prod_full_norm:
            return prod

        # Check aliases
        for alias in prod_aliases:
            alias_norm = _normalize_string(alias)
            if model_clean == alias or model_norm == alias_norm:
                return prod
            # Unambiguous word boundary match for specific model identifiers (e.g. "5420", "t14", "840")
            if len(alias) >= 3 and re.search(r"\b" + re.escape(alias) + r"\b", model_clean):
                return prod
            if len(alias_norm) >= 4 and alias_norm in model_norm:
                return prod

    return None


def get_model_spec(model_or_slug: str) -> dict:
    """
    Retrieves full structured specification dictionary for a given model or slug.
    Raises AppError(UNSUPPORTED_MODEL) if the model cannot be resolved.
    """
    if not model_or_slug or not model_or_slug.strip():
        raise AppError(
            code=UNSUPPORTED_MODEL,
            message="Model query cannot be empty.",
            field="model",
            http_status=400,
        )

    products = load_all_products()
    query = model_or_slug.strip().lower()
    query_norm = _normalize_string(query)

    # 1. Exact slug match
    if query in products:
        return products[query]

    # 2. Check aliases and exact model name
    for slug, prod in products.items():
        if prod.get("slug", "").lower() == query:
            return prod

        full_name = f"{prod.get('manufacturer', '')} {prod.get('model', '')}".lower()
        if query == full_name or query == prod.get("model", "").lower():
            return prod

        # Check aliases
        aliases = prod.get("aliases", [])
        for alias in aliases:
            if query == alias.lower() or query_norm == _normalize_string(alias):
                return prod

    # 3. Fuzzy / substring normalized match
    for slug, prod in products.items():
        slug_norm = _normalize_string(slug)
        full_name_norm = _normalize_string(f"{prod.get('manufacturer', '')} {prod.get('model', '')}")
        model_norm = _normalize_string(prod.get("model", ""))

        if query_norm in full_name_norm or full_name_norm in query_norm:
            return prod
        if query_norm in slug_norm or slug_norm in query_norm:
            return prod
        if query_norm in model_norm or model_norm in query_norm:
            return prod

    # If no match found, raise standard typed error
    raise AppError(
        code=UNSUPPORTED_MODEL,
        message=f"Model '{model_or_slug}' is not supported in the knowledge catalog. Supported models include: {', '.join(p['model'] for p in products.values())}.",
        field="model",
        http_status=400,
    )


def get_repair_cost(model_or_slug: str, component: str) -> dict:
    """
    Retrieves repair cost range in INR for a specific component of a given model.
    Every number carries basis: 'assumption' and an explanatory note.
    Raises AppError(UNSUPPORTED_MODEL) if model is not supported.
    """
    spec = get_model_spec(model_or_slug)
    costs = spec.get("typical_repair_cost_inr", {})
    comp_key = component.strip().lower()

    # Normalize component names
    comp_map = {
        "battery": "battery",
        "ssd": "ssd",
        "storage": "ssd",
        "ram": "ram",
        "memory": "ram",
        "keyboard": "keyboard",
        "thermal": "thermals",
        "thermals": "thermals",
        "fan": "thermals",
        "screen": "display",
        "display": "display",
        "motherboard": "motherboard",
        "system": "motherboard",
        "logic_board": "motherboard",
    }

    normalized_comp = comp_map.get(comp_key, comp_key)

    if normalized_comp in costs:
        return costs[normalized_comp]

    # Fallback with explicit assumption
    return {
        "min": 1000,
        "max": 3000,
        "basis": "assumption",
        "note": f"Default estimated repair cost assumption for {component} on {spec.get('model')}.",
    }


def get_useful_life(model_or_slug: str) -> dict:
    """
    Retrieves useful life assumptions for a given model.
    Raises AppError(UNSUPPORTED_MODEL) if model is not supported.
    """
    spec = get_model_spec(model_or_slug)
    useful_life = spec.get("expected_useful_life")
    if useful_life:
        return useful_life

    return {
        "baseline_years": 5.0,
        "extended_years_post_repair": 2.5,
        "basis": "assumption",
        "note": f"Standard estimated enterprise useful life baseline for {spec.get('model')}.",
    }


def get_model_spec_or_generic(
    model_or_slug: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
) -> tuple[dict, bool]:
    """
    Attempts to match a specific catalog model. If matched, returns (spec_dict, False).
    If not matched, falls back to the generic laptop profile and returns (generic_dict, True).
    """
    # 1. Try match by manufacturer + model
    if manufacturer and model:
        match = match_catalog_model(manufacturer, model)
        if match:
            return match, False

    # 2. Try match by model_or_slug query
    if model_or_slug:
        try:
            spec = get_model_spec(model_or_slug)
            return spec, False
        except Exception:
            pass

    # 3. Fallback to generic
    return get_generic_laptop_profile(), True


def get_repair_cost_with_fallback(
    model_or_slug: Optional[str] = None,
    component: str = "battery",
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """
    Retrieves repair cost for a component. If the device matches a catalog entry,
    returns precise costs with basis: 'assumption'.
    If not, returns category-level estimates with basis: 'GENERIC_CATEGORY_ESTIMATE'.
    """
    spec, is_generic = get_model_spec_or_generic(
        model_or_slug=model_or_slug,
        manufacturer=manufacturer,
        model=model,
    )
    costs = spec.get("typical_repair_cost_inr", {})
    comp_key = component.strip().lower()

    comp_map = {
        "battery": "battery",
        "ssd": "ssd",
        "storage": "ssd",
        "ram": "ram",
        "memory": "ram",
        "keyboard": "keyboard",
        "thermal": "thermals",
        "thermals": "thermals",
        "fan": "thermals",
        "screen": "display",
        "display": "display",
        "motherboard": "motherboard",
        "system": "motherboard",
        "logic_board": "motherboard",
    }
    normalized_comp = comp_map.get(comp_key, comp_key)

    if normalized_comp in costs:
        cost_item = dict(costs[normalized_comp])
        if is_generic:
            cost_item["basis"] = "GENERIC_CATEGORY_ESTIMATE"
        return cost_item

    basis_val = "GENERIC_CATEGORY_ESTIMATE" if is_generic else "assumption"
    return {
        "min": 1500,
        "max": 3500,
        "basis": basis_val,
        "note": f"Estimated repair cost for {component} on {spec.get('model', 'General Laptop')}.",
    }


def get_useful_life_with_fallback(
    model_or_slug: Optional[str] = None,
    manufacturer: Optional[str] = None,
    model: Optional[str] = None,
) -> dict:
    """
    Retrieves useful life assumptions. If model matches catalog, returns precise data.
    If not, returns category-level estimate with basis: 'GENERIC_CATEGORY_ESTIMATE'.
    """
    spec, is_generic = get_model_spec_or_generic(
        model_or_slug=model_or_slug,
        manufacturer=manufacturer,
        model=model,
    )
    useful_life = spec.get("expected_useful_life")
    if useful_life:
        life_item = dict(useful_life)
        if is_generic:
            life_item["basis"] = "GENERIC_CATEGORY_ESTIMATE"
        return life_item

    basis_val = "GENERIC_CATEGORY_ESTIMATE" if is_generic else "assumption"
    return {
        "baseline_years": 5.0,
        "extended_years_post_repair": 2.5,
        "basis": basis_val,
        "note": f"Estimated useful life baseline for {spec.get('model', 'General Laptop')}.",
    }
