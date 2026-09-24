from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import api_router
from app.config import settings

app = FastAPI(
    title="ReLoop AI API",
    description="Product-life extension decision engine API",
    version="0.1.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes under /api
app.include_router(api_router, prefix="/api")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}
