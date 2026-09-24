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
    ]
    for p in candidates:
        if p.exists() and p.is_dir():
            return p
    return candidates[0]


_PRODUCTS_CACHE: Optional[Dict[str, dict]] = None


def load_all_products(force_reload: bool = False) -> Dict[str, dict]:
    """
    Loads all product JSON files into an in-memory dictionary keyed by slug.
    """
    global _PRODUCTS_CACHE
    if _PRODUCTS_CACHE is not None and not force_reload:
        return _PRODUCTS_CACHE

    products_dir = get_products_data_dir()
    cache: Dict[str, dict] = {}

    if products_dir.exists():
        for json_file in products_dir.glob("*.json"):
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
