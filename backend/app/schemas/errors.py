"""
Re-export from app.errors for backwards compatibility.
"""
from app.errors import (
    AppError,
    AppException,
    ErrorCode,
    ErrorDetail,
    ErrorResponse,
    INVALID_INPUT,
    UNSUPPORTED_MODEL,
    INVALID_DIAGNOSTIC,
    AI_FAILURE,
    MISSING_EVIDENCE,
    INVALID_PATHWAY_CALC,
    NOT_FOUND,
    INTERNAL_ERROR,
    VALIDATION_ERROR,
    OTP_EXPIRED,
    OTP_INVALID,
    OTP_ATTEMPTS_EXCEEDED,
    RATE_LIMITED,
)

__all__ = [
    "AppError",
    "AppException",
    "ErrorCode",
    "ErrorDetail",
    "ErrorResponse",
    "INVALID_INPUT",
    "UNSUPPORTED_MODEL",
    "INVALID_DIAGNOSTIC",
    "AI_FAILURE",
    "MISSING_EVIDENCE",
    "INVALID_PATHWAY_CALC",
    "NOT_FOUND",
    "INTERNAL_ERROR",
    "VALIDATION_ERROR",
    "OTP_EXPIRED",
    "OTP_INVALID",
    "OTP_ATTEMPTS_EXCEEDED",
    "RATE_LIMITED",
]
