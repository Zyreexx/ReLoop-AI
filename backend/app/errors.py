"""
Application errors, standard error codes, and global exception handlers.
Strictly conforms to docs/rules.md and architecture requirements:
All errors return:
{
  "error": {
    "code": "...",
    "message": "...",
    "field": "..."
  }
}
"""
import logging
from enum import Enum
from typing import Optional
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    INVALID_INPUT = "INVALID_INPUT"
    UNSUPPORTED_MODEL = "UNSUPPORTED_MODEL"
    INVALID_DIAGNOSTIC = "INVALID_DIAGNOSTIC"
    AI_FAILURE = "AI_FAILURE"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    INVALID_PATHWAY_CALC = "INVALID_PATHWAY_CALC"
    NOT_FOUND = "NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    OTP_EXPIRED = "OTP_EXPIRED"
    OTP_INVALID = "OTP_INVALID"
    OTP_ATTEMPTS_EXCEEDED = "OTP_ATTEMPTS_EXCEEDED"
    RATE_LIMITED = "RATE_LIMITED"


# Convenience constants
INVALID_INPUT = ErrorCode.INVALID_INPUT.value
UNSUPPORTED_MODEL = ErrorCode.UNSUPPORTED_MODEL.value
INVALID_DIAGNOSTIC = ErrorCode.INVALID_DIAGNOSTIC.value
AI_FAILURE = ErrorCode.AI_FAILURE.value
MISSING_EVIDENCE = ErrorCode.MISSING_EVIDENCE.value
INVALID_PATHWAY_CALC = ErrorCode.INVALID_PATHWAY_CALC.value
NOT_FOUND = ErrorCode.NOT_FOUND.value
INTERNAL_ERROR = ErrorCode.INTERNAL_ERROR.value
VALIDATION_ERROR = ErrorCode.VALIDATION_ERROR.value
OTP_EXPIRED = ErrorCode.OTP_EXPIRED.value
OTP_INVALID = ErrorCode.OTP_INVALID.value
OTP_ATTEMPTS_EXCEEDED = ErrorCode.OTP_ATTEMPTS_EXCEEDED.value
RATE_LIMITED = ErrorCode.RATE_LIMITED.value


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    error: ErrorDetail


class AppError(Exception):
    """
    Standard typed domain error for ReLoop AI.
    """
    def __init__(
        self,
        code: str,
        message: str,
        field: Optional[str] = None,
        http_status: int = 400,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.field = field
        self.http_status = http_status
        # Backwards compatibility property
        self.status_code = http_status

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "field": self.field,
            }
        }


# Backwards compatibility alias
AppException = AppError


from starlette.exceptions import HTTPException as StarletteHTTPException


def register_error_handlers(app: FastAPI) -> None:
    """
    Registers global exception handlers on the FastAPI app.
    Guarantees every error returns: {"error": {"code", "message", "field"}}.
    Unhandled exceptions return generic INTERNAL_ERROR with no stack trace.
    """

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.http_status,
            content=exc.to_dict(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        errors = exc.errors()
        first_err = errors[0] if errors else {}
        loc_parts = [str(item) for item in first_err.get("loc", []) if item != "body"]
        field_name = ".".join(loc_parts) if loc_parts else None

        msg = first_err.get("msg", "Invalid request input.")
        if "Value error, " in msg:
            msg = msg.replace("Value error, ", "")

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": ErrorCode.INVALID_INPUT.value,
                    "message": msg,
                    "field": field_name,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        code = (
            ErrorCode.NOT_FOUND.value
            if exc.status_code == 404
            else (
                ErrorCode.RATE_LIMITED.value
                if exc.status_code == 429
                else (
                    ErrorCode.INVALID_INPUT.value
                    if exc.status_code in [400, 422]
                    else ErrorCode.INTERNAL_ERROR.value
                )
            )
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": str(exc.detail),
                    "field": None,
                }
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled server error on {request.url.path}: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "An unexpected internal server error occurred.",
                    "field": None,
                }
            },
        )

