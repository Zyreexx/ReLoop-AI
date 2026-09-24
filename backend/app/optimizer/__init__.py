"""
Deterministic circular path optimizer.
Notice: This package strictly imports NO AI modules.
"""
from app.optimizer.rules import (
    evaluate_repair_eligibility,
    evaluate_upgrade_eligibility,
    evaluate_refurbish_eligibility,
    evaluate_reuse_redeploy_eligibility,
    evaluate_component_recovery_eligibility,
    evaluate_recycle_eligibility,
)
from app.optimizer.pathways import generate_all_pathways
from app.optimizer.scorer import score_pathways, OBJECTIVE_WEIGHTS

__all__ = [
    "evaluate_repair_eligibility",
    "evaluate_upgrade_eligibility",
    "evaluate_refurbish_eligibility",
    "evaluate_reuse_redeploy_eligibility",
    "evaluate_component_recovery_eligibility",
    "evaluate_recycle_eligibility",
    "generate_all_pathways",
    "score_pathways",
    "OBJECTIVE_WEIGHTS",
]
