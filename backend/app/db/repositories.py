"""
Repository layer providing clean CRUD operations for Products, Evidence, Assessments, and Recommendations.
Handles seamless translation between SQLAlchemy models and Pydantic schemas.
"""
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.entities import (
    Product as ProductModel,
    Assessment as AssessmentModel,
    Evidence as EvidenceModel,
    ComponentConditionRecord as ComponentConditionModel,
    RecommendationRecord as RecommendationModel,
)
from app.schemas.product import Product, ProductCreate, ProductSpecs
from app.schemas.evidence import Evidence
from app.schemas.condition import AssessmentBuildResponse, ComponentCondition
from app.schemas.recommendation import Recommendation, RecommendationExplanation, ScoredPathway, SecondLifeSuggestion, ComponentRecoveryManifest
from app.schemas.pathway import Pathway
from app.schemas.enums import (
    ComponentName,
    ComponentStatus,
    ConfidenceLevel,
    DeviceCategory,
    EvidenceType,
    Objective,
    PathwayType,
)


class ProductRepository:
    @staticmethod
    def create(db: Session, data: ProductCreate | Product) -> Product:
        if isinstance(data, Product):
            prod_id = data.id
            specs_dict = data.specs.model_dump() if hasattr(data.specs, "model_dump") else data.specs
            age = data.age
            cat = data.category.value if hasattr(data.category, "value") else str(data.category)
            entity = ProductModel(
                id=prod_id,
                manufacturer=data.manufacturer,
                model=data.model,
                model_year=data.model_year,
                category=cat,
                serial_or_identifier=data.serial_or_identifier,
                age=age,
                specs=specs_dict,
                created_at=data.created_at,
            )
        else:
            specs_dict = ProductSpecs().model_dump()
            age = data.age_years if data.age_years is not None else (data.age if data.age is not None else max(0.5, float(2026 - data.model_year)))
            cat = data.category.value if hasattr(data.category, "value") else str(data.category)
            entity = ProductModel(
                manufacturer=data.manufacturer,
                model=data.model,
                model_year=data.model_year,
                category=cat,
                serial_or_identifier=data.serial_or_identifier,
                age=age,
                specs=specs_dict,
            )

        db.add(entity)
        db.commit()
        db.refresh(entity)
        return ProductRepository._to_schema(entity)

    @staticmethod
    def get_by_id(db: Session, product_id: str) -> Optional[Product]:
        entity = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not entity:
            return None
        return ProductRepository._to_schema(entity)

    @staticmethod
    def _to_schema(entity: ProductModel) -> Product:
        specs_obj = ProductSpecs(**(entity.specs or {})) if entity.specs else ProductSpecs()
        return Product(
            id=entity.id,
            manufacturer=entity.manufacturer,
            model=entity.model,
            model_year=entity.model_year,
            category=DeviceCategory(entity.category) if entity.category in DeviceCategory._value2member_map_ else DeviceCategory.LAPTOP,
            serial_or_identifier=entity.serial_or_identifier,
            age=entity.age,
            specs=specs_obj,
            created_at=entity.created_at,
        )


class EvidenceRepository:
    @staticmethod
    def add(
        db: Session,
        evidence: Evidence,
        product_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
    ) -> Evidence:
        p_id = product_id or evidence.product_id
        type_str = evidence.type.value if hasattr(evidence.type, "value") else str(evidence.type)
        conf_str = evidence.confidence.value if hasattr(evidence.confidence, "value") else str(evidence.confidence)

        entity = EvidenceModel(
            id=evidence.id,
            product_id=p_id,
            assessment_id=assessment_id,
            type=type_str,
            source_reference=evidence.source,
            component=evidence.component,
            value=evidence.value,
            confidence=conf_str,
            timestamp=evidence.timestamp,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return EvidenceRepository._to_schema(entity)

    @staticmethod
    def add_batch(
        db: Session,
        evidences: List[Evidence],
        product_id: Optional[str] = None,
        assessment_id: Optional[str] = None,
    ) -> List[Evidence]:
        result = []
        for ev in evidences:
            result.append(EvidenceRepository.add(db, ev, product_id=product_id, assessment_id=assessment_id))
        return result

    @staticmethod
    def get_by_product_id(db: Session, product_id: str) -> List[Evidence]:
        entities = (
            db.query(EvidenceModel)
            .filter(EvidenceModel.product_id == product_id)
            .order_by(EvidenceModel.timestamp.asc())
            .all()
        )
        return [EvidenceRepository._to_schema(e) for e in entities]

    @staticmethod
    def _to_schema(entity: EvidenceModel) -> Evidence:
        ev_type = EvidenceType(entity.type) if entity.type in EvidenceType._value2member_map_ else EvidenceType.DATABASE
        conf = ConfidenceLevel(entity.confidence) if entity.confidence in ConfidenceLevel._value2member_map_ else ConfidenceLevel.HIGH
        return Evidence(
            id=entity.id,
            product_id=entity.product_id,
            type=ev_type,
            source=entity.source_reference,
            component=entity.component,
            value=entity.value,
            confidence=conf,
            timestamp=entity.timestamp,
        )


class AssessmentRepository:
    @staticmethod
    def save(db: Session, assessment: AssessmentBuildResponse) -> AssessmentBuildResponse:
        # Check if assessment exists for product
        existing = (
            db.query(AssessmentModel)
            .filter(
                (AssessmentModel.product_id == assessment.product_id)
            )
            .first()
        )
        if existing:
            db.delete(existing)
            db.commit()

        entity = AssessmentModel(
            product_id=assessment.product_id,
            overall_hardware_health=assessment.overall_hardware_health,
            created_at=assessment.created_at,
        )
        db.add(entity)
        db.flush()

        # Add ComponentConditionRecords
        for comp_key, comp in assessment.components.items():
            comp_name_str = comp.component.value if hasattr(comp.component, "value") else str(comp.component)
            status_str = comp.status.value if hasattr(comp.status, "value") else str(comp.status)
            conf_str = comp.confidence.value if hasattr(comp.confidence, "value") else str(comp.confidence)

            comp_rec = ComponentConditionModel(
                assessment_id=entity.id,
                component=comp_key,  # Keep original key (e.g. 'battery', 'ssd')
                status=status_str,
                observations=comp.observations,
                measurements=comp.measurements,
                confidence=conf_str,
                evidence_ids=comp.evidence_ids,
                label=comp.label,
                repairable=comp.repairable,
                upgradeable=comp.upgradeable,
            )
            db.add(comp_rec)

        # Persist all evidence associated with this assessment
        if assessment.all_evidence:
            for ev in assessment.all_evidence:
                ev_type = ev.type.value if hasattr(ev.type, "value") else str(ev.type)
                ev_conf = ev.confidence.value if hasattr(ev.confidence, "value") else str(ev.confidence)
                ev_existing = db.query(EvidenceModel).filter(EvidenceModel.id == ev.id).first()
                if not ev_existing:
                    ev_entity = EvidenceModel(
                        id=ev.id,
                        product_id=assessment.product_id,
                        assessment_id=entity.id,
                        type=ev_type,
                        source_reference=ev.source,
                        component=ev.component,
                        value=ev.value,
                        confidence=ev_conf,
                        timestamp=ev.timestamp,
                    )
                    db.add(ev_entity)

        db.commit()
        db.refresh(entity)
        return AssessmentRepository._to_schema(entity, db)

    @staticmethod
    def get_by_product_id(db: Session, product_id: str) -> Optional[AssessmentBuildResponse]:
        entity = (
            db.query(AssessmentModel)
            .filter(AssessmentModel.product_id == product_id)
            .order_by(AssessmentModel.created_at.desc())
            .first()
        )
        if not entity:
            return None
        return AssessmentRepository._to_schema(entity, db)

    @staticmethod
    def get_by_id(db: Session, assessment_id: str) -> Optional[AssessmentBuildResponse]:
        entity = db.query(AssessmentModel).filter(AssessmentModel.id == assessment_id).first()
        if not entity:
            return None
        return AssessmentRepository._to_schema(entity, db)

    @staticmethod
    def _to_schema(entity: AssessmentModel, db: Session) -> AssessmentBuildResponse:
        comp_records = (
            db.query(ComponentConditionModel)
            .filter(ComponentConditionModel.assessment_id == entity.id)
            .all()
        )
        components_map: Dict[str, ComponentCondition] = {}
        for c in comp_records:
            c_name = ComponentName(c.component) if c.component in ComponentName._value2member_map_ else c.component
            c_status = ComponentStatus(c.status) if c.status in ComponentStatus._value2member_map_ else ComponentStatus.UNKNOWN
            c_conf = ConfidenceLevel(c.confidence) if c.confidence in ConfidenceLevel._value2member_map_ else ConfidenceLevel.HIGH

            cond_obj = ComponentCondition(
                component=c_name,
                status=c_status,
                observations=c.observations or [],
                measurements=c.measurements or {},
                confidence=c_conf,
                evidence_ids=c.evidence_ids or [],
                label=c.label,
                repairable=c.repairable,
                upgradeable=c.upgradeable,
            )
            components_map[c.component] = cond_obj
            components_map[c.component.lower()] = cond_obj

        evidences = EvidenceRepository.get_by_product_id(db, entity.product_id)

        return AssessmentBuildResponse(
            product_id=entity.product_id,
            overall_hardware_health=entity.overall_hardware_health,
            components=components_map,
            all_evidence=evidences,
            created_at=entity.created_at,
        )


class RecommendationRepository:
    @staticmethod
    def save(db: Session, rec: Recommendation) -> Recommendation:
        p_pathway = rec.selected_pathway.value if hasattr(rec.selected_pathway, "value") else str(rec.selected_pathway)
        obj_str = rec.objective.value if hasattr(rec.objective, "value") else str(rec.objective)

        entity = RecommendationModel(
            id=rec.id,
            product_id=rec.product_id,
            selected_pathway=p_pathway,
            objective=obj_str,
            score=rec.score,
            alternative_pathways=[
                (p.model_dump() if hasattr(p, "model_dump") else p)
                for p in rec.alternative_pathways
            ],
            reasoning=rec.reasoning,
            evidence_ids=rec.evidence_ids,
            assumptions=rec.assumptions,
            primary_recommendation=(
                rec.primary_recommendation.model_dump()
                if hasattr(rec.primary_recommendation, "model_dump")
                else rec.primary_recommendation
            ),
            explanation=(
                rec.explanation.model_dump()
                if hasattr(rec.explanation, "model_dump")
                else rec.explanation
            ),
            second_life=(
                rec.second_life.model_dump()
                if hasattr(rec.second_life, "model_dump")
                else rec.second_life
            ),
            component_recovery=(
                rec.component_recovery.model_dump()
                if hasattr(rec.component_recovery, "model_dump")
                else rec.component_recovery
            ),
            created_at=rec.created_at,
        )
        db.add(entity)
        db.commit()
        db.refresh(entity)
        return rec

    @staticmethod
    def get_by_id(db: Session, recommendation_id: str) -> Optional[Recommendation]:
        entity = (
            db.query(RecommendationModel)
            .filter(RecommendationModel.id == recommendation_id)
            .first()
        )
        if not entity:
            return None
        return RecommendationRepository._to_schema(entity)

    @staticmethod
    def get_by_product_id(db: Session, product_id: str) -> Optional[Recommendation]:
        entity = (
            db.query(RecommendationModel)
            .filter(RecommendationModel.product_id == product_id)
            .order_by(RecommendationModel.created_at.desc())
            .first()
        )
        if not entity:
            return None
        return RecommendationRepository._to_schema(entity)

    @staticmethod
    def _to_schema(entity: RecommendationModel) -> Recommendation:
        p_type = PathwayType(entity.selected_pathway) if entity.selected_pathway in PathwayType._value2member_map_ else PathwayType.REPAIR
        obj = Objective(entity.objective) if entity.objective in Objective._value2member_map_ else Objective.MAX_LIFE

        primary_rec = None
        if entity.primary_recommendation:
            primary_rec = ScoredPathway(**entity.primary_recommendation) if isinstance(entity.primary_recommendation, dict) else entity.primary_recommendation

        explanation = None
        if entity.explanation:
            explanation = RecommendationExplanation(**entity.explanation) if isinstance(entity.explanation, dict) else entity.explanation

        second_life = None
        if entity.second_life:
            second_life = SecondLifeSuggestion(**entity.second_life) if isinstance(entity.second_life, dict) else entity.second_life

        recovery = None
        if entity.component_recovery:
            recovery = ComponentRecoveryManifest(**entity.component_recovery) if isinstance(entity.component_recovery, dict) else entity.component_recovery

        return Recommendation(
            id=entity.id,
            product_id=entity.product_id,
            selected_pathway=p_type,
            objective=obj,
            score=entity.score,
            alternative_pathways=entity.alternative_pathways or [],
            reasoning=entity.reasoning or [],
            evidence_ids=entity.evidence_ids or [],
            assumptions=entity.assumptions or [],
            primary_recommendation=primary_rec,
            explanation=explanation,
            second_life=second_life,
            component_recovery=recovery,
            created_at=entity.created_at,
        )


product_repo = ProductRepository()
evidence_repo = EvidenceRepository()
assessment_repo = AssessmentRepository()
recommendation_repo = RecommendationRepository()
