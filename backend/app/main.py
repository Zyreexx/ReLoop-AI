"""
ReLoop AI Backend — FastAPI Application Entrypoint.
The Next-Life Engine for Products.
"""
import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.api.routes import api_router
from contextlib import asynccontextmanager
from app.db.session import create_all_tables
import logging

logger = logging.getLogger("reloop-ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Creating database tables on startup...")
        create_all_tables()
    except Exception as e:
        logger.warning(f"Could not initialize database tables on startup: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="The Next-Life Engine for Products — Circular Decision and Optimization Layer",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


@app.get("/health")
def root_health():
    return {"status": "ok"}

import time
from uuid import uuid4
from fastapi import Response

# CORS Middleware (Restricted to configured origins from env, not wildcard)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):
    """
    Structured request logging middleware:
    - Generates/propagates X-Request-ID
    - Measures duration in ms
    - Logs method, path, status, and duration without logging sensitive body payloads
    - Intercepts unhandled exceptions to return consistent {"error": {"code", "message", "field"}}
    """
    request_id = request.headers.get("x-request-id") or f"req_{uuid4().hex[:12]}"
    start_time = time.perf_counter()

    try:
        response: Response = await call_next(request)
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(
            f"request_id={request_id} method={request.method} path={request.url.path} "
            f"status=500 duration_ms={duration_ms:.2f}",
            exc_info=True,
        )
        response = JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "field": None,
                }
            },
        )

    duration_ms = (time.perf_counter() - start_time) * 1000.0
    response.headers["X-Request-ID"] = request_id

    logger.info(
        f"request_id={request_id} method={request.method} path={request.url.path} "
        f"status={response.status_code} duration_ms={duration_ms:.2f}"
    )
    return response


# Register global error handlers per docs/rules.md
from app.errors import register_error_handlers
register_error_handlers(app)


# Register API Routers
app.include_router(api_router)


@app.get("/")
def root():
    return {
        "message": "ReLoop AI — The Next-Life Engine for Products",
        "documentation": "/docs",
        "health": "/api/health",
        "version": settings.VERSION,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
