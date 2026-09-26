"""
Configuration settings for ReLoop AI Backend.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PROJECT_NAME: str = "ReLoop AI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    MAX_UPLOAD_MB: int = 10
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./reloop.db"
    )

    # CORS
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ]

    # Gemini
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    # Fallback mode for demo deployment / Gemini failure
    DEMO_FALLBACK: bool = os.getenv("DEMO_FALLBACK", "false").lower() in (
        "true",
        "1",
        "yes",
    )


settings = Settings()
