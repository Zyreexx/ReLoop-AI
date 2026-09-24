"""
SQLAlchemy ORM models for ReLoop AI persistence:
Product, Assessment, Evidence, ComponentConditionRecord, RecommendationRecord.
"""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String(50), primary_key=True, default=lambda: f"prod_{uuid4().hex[:10]}")
    manufacturer = Column(String(100), nullable=False)
    model = Column(String(150), nullable=False)
    model_year = Column(Integer, nullable=False)
    category = Column(String(50), default="LAPTOP", nullable=False)
    serial_or_identifier = Column(String(100), nullable=True)
    age = Column(Float, nullable=False)
    specs = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    assessments = relationship(
        "Assessment", back_populates="product", cascade="all, delete-orphan"
    )
    evidences = relationship(
        "Evidence", back_populates="product", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "RecommendationRecord", back_populates="product", cascade="all, delete-orphan"
    )


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String(50), primary_key=True, default=lambda: f"asm_{uuid4().hex[:10]}")
    product_id = Column(
        String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True
    )
    overall_hardware_health = Column(String(50), default="FAIR", nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="assessments")
    components = relationship(
        "ComponentConditionRecord",
        back_populates="assessment",
        cascade="all, delete-orphan",
    )
    evidences = relationship(
        "Evidence", back_populates="assessment", cascade="all, delete-orphan"
    )
    recommendations = relationship(
        "RecommendationRecord", back_populates="assessment", cascade="all, delete-orphan"
    )


class Evidence(Base):
    __tablename__ = "evidence_records"

    id = Column(String(50), primary_key=True, default=lambda: f"ev_{uuid4().hex[:10]}")
    product_id = Column(
        String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    assessment_id = Column(
        String(50), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    type = Column(String(50), nullable=False)  # VISUAL, DIAGNOSTIC, USER_REPORTED, DATABASE, ESTIMATE
    source_reference = Column(String(255), nullable=False)
    component = Column(String(50), nullable=True)
    value = Column(JSON, nullable=False)
    confidence = Column(String(50), default="HIGH", nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="evidences")
    assessment = relationship("Assessment", back_populates="evidences")


class ComponentConditionRecord(Base):
    __tablename__ = "component_condition_records"

    id = Column(String(50), primary_key=True, default=lambda: f"comp_{uuid4().hex[:10]}")
    assessment_id = Column(
        String(50), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    component = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)
    observations = Column(JSON, nullable=True)
    measurements = Column(JSON, nullable=True)
    confidence = Column(String(50), default="HIGH", nullable=False)
    evidence_ids = Column(JSON, nullable=True)
    label = Column(String(255), nullable=True)
    repairable = Column(Boolean, default=True, nullable=False)
    upgradeable = Column(Boolean, default=False, nullable=False)

    # Relationships
    assessment = relationship("Assessment", back_populates="components")


class RecommendationRecord(Base):
    __tablename__ = "recommendation_records"

    id = Column(String(50), primary_key=True, default=lambda: f"rec_{uuid4().hex[:10]}")
    product_id = Column(
        String(50), ForeignKey("products.id", ondelete="CASCADE"), nullable=True, index=True
    )
    assessment_id = Column(
        String(50), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=True, index=True
    )
    selected_pathway = Column(String(50), nullable=False)
    objective = Column(String(50), nullable=False)
    score = Column(Float, nullable=False)
    alternative_pathways = Column(JSON, nullable=True)
    reasoning = Column(JSON, nullable=True)
    evidence_ids = Column(JSON, nullable=True)
    assumptions = Column(JSON, nullable=True)
    primary_recommendation = Column(JSON, nullable=True)
    second_life = Column(JSON, nullable=True)
    component_recovery = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    product = relationship("Product", back_populates="recommendations")
    assessment = relationship("Assessment", back_populates="recommendations")
