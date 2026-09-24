"""
Knowledge module providing structured catalog, model specifications,
repair costs, and lifecycle assumptions.
"""
from app.knowledge.loader import (
    get_demo_data_dir,
    get_model_spec,
    get_products_data_dir,
    get_repair_cost,
    get_supported_models,
    get_supported_product_candidates,
    get_useful_life,
    load_all_products,
)

__all__ = [
    "get_supported_models",
    "get_supported_product_candidates",
    "get_model_spec",
    "get_repair_cost",
    "get_useful_life",
    "load_all_products",
    "get_products_data_dir",
    "get_demo_data_dir",
]
