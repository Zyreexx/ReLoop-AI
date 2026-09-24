"""
Database package init exporting base, engine, session, and repositories.
"""
from app.db.base import Base
from app.db.session import engine, SessionLocal, get_db, create_all_tables
from app.db.repositories import (
    ProductRepository,
    EvidenceRepository,
    AssessmentRepository,
    RecommendationRepository,
    product_repo,
    evidence_repo,
    assessment_repo,
    recommendation_repo,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "create_all_tables",
    "ProductRepository",
    "EvidenceRepository",
    "AssessmentRepository",
    "RecommendationRepository",
    "product_repo",
    "evidence_repo",
    "assessment_repo",
    "recommendation_repo",
]
