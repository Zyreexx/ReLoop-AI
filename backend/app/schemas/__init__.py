"""
Pydantic v2 schemas and domain models for ReLoop AI.
"""
from app.schemas.enums import (
    EvidenceType,
    ComponentName,
    ComponentStatus,
    PathwayType,
    Objective,
    ObjectiveType,
    ConfidenceLevel,
    DeviceCategory,
)
from app.schemas.estimate import Estimate, RangeEstimate
from app.schemas.evidence import Evidence, EvidenceItem
from app.schemas.product import (
    Product,
    ProductRecord,
    ProductSpecs,
    ProductCandidate,
    ProductCreate,
    ProductIdentifyRequest,
    ProductIdentifyResponse,
    ProductIdentificationRequest,
    ProductIdentificationResponse,
)
from app.schemas.diagnostics import (
    BatteryDiagnostic,
    SsdDiagnostic,
    RamDiagnostic,
    ThermalDiagnostic,
    SystemDiagnostic,
    DiagnosticsValidateRequest,
    DiagnosticsValidateResponse,
    DiagnosticsInput,
    DiagnosticValidationResult,
)
from app.schemas.condition import (
    ComponentCondition,
    AssessmentBuildRequest,
    AssessmentBuildResponse,
    ConditionProfile,
    BuildAssessmentRequest,
)
from app.schemas.pathway import (
    Pathway,
    PathwayOption,
    PathwayEligibility,
    EnvironmentalEstimate,
    LogisticsEstimate,
)
from app.schemas.recommendation import (
    Recommendation,
    RecommendationResponse,
    RecommendationsGenerateRequest,
    RecommendationsGenerateResponse,
    RecommendationRequest,
    ReportResponse,
    ScoredPathway,
    SecondLifeSuggestion,
    ComponentRecoveryManifest,
)
from app.schemas.symptoms import (
    SymptomsParseRequest,
    SymptomsParseResponse,
    SymptomInput,
    SymptomParseResult,
    ParsedSymptomItem,
)
from app.schemas.vision import (
    VisionAnalyzeRequest,
    VisionAnalyzeResponse,
    VisionAnalysisRequest,
    VisionAnalysisResponse,
    VisualComponentFinding,
)
from app.errors import (
    AppError,
    AppException,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
)

__all__ = [
    # Enums
    "EvidenceType",
    "ComponentName",
    "ComponentStatus",
    "PathwayType",
    "Objective",
    "ObjectiveType",
    "ConfidenceLevel",
    "DeviceCategory",
    # Core Architecture section 6 models
    "Product",
    "ProductRecord",
    "Evidence",
    "EvidenceItem",
    "ComponentCondition",
    "Pathway",
    "PathwayOption",
    "Recommendation",
    "RecommendationResponse",
    # Reusable Estimate
    "Estimate",
    "RangeEstimate",
    # Endpoint Request/Responses (Section 9)
    "ProductIdentifyRequest",
    "ProductIdentifyResponse",
    "ProductIdentificationRequest",
    "ProductIdentificationResponse",
    "ProductCreate",
    "ProductCandidate",
    "ProductSpecs",
    "VisionAnalyzeRequest",
    "VisionAnalyzeResponse",
    "VisionAnalysisRequest",
    "VisionAnalysisResponse",
    "VisualComponentFinding",
    "DiagnosticsValidateRequest",
    "DiagnosticsValidateResponse",
    "DiagnosticsInput",
    "DiagnosticValidationResult",
    "BatteryDiagnostic",
    "SsdDiagnostic",
    "RamDiagnostic",
    "ThermalDiagnostic",
    "SystemDiagnostic",
    "SymptomsParseRequest",
    "SymptomsParseResponse",
    "SymptomInput",
    "SymptomParseResult",
    "ParsedSymptomItem",
    "AssessmentBuildRequest",
    "AssessmentBuildResponse",
    "ConditionProfile",
    "BuildAssessmentRequest",
    "RecommendationsGenerateRequest",
    "RecommendationsGenerateResponse",
    "RecommendationRequest",
    "ReportResponse",
    "PathwayEligibility",
    "EnvironmentalEstimate",
    "LogisticsEstimate",
    "ScoredPathway",
    "SecondLifeSuggestion",
    "ComponentRecoveryManifest",
    # Errors
    "AppError",
    "AppException",
    "ErrorCode",
    "ErrorDetail",
    "ErrorResponse",
]
