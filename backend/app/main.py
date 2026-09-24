"""
ReLoop AI Backend — FastAPI Application Entrypoint.
The Next-Life Engine for Products.
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.schemas.errors import AppException
from app.api.routes import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="The Next-Life Engine for Products — Circular Decision and Optimization Layer",
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
