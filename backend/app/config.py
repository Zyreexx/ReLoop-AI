"""
Configuration settings for ReLoop AI Backend.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Load backend/.env and root .env so configurations in either location are resolved
backend_env = Path(__file__).resolve().parent.parent / ".env"
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if backend_env.exists():
    load_dotenv(backend_env, override=True)
if root_env.exists():
    load_dotenv(root_env, override=True)
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
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    GEMINI_MEDIA_RESOLUTION: str = os.getenv("GEMINI_MEDIA_RESOLUTION", "HIGH")
    MAX_IDENTIFY_IMAGES: int = int(os.getenv("MAX_IDENTIFY_IMAGES", "5"))

    # Fallback mode for demo deployment / Gemini failure
    DEMO_FALLBACK: bool = os.getenv("DEMO_FALLBACK", "false").lower() in (
        "true",
        "1",
        "yes",
    )

    # Resend
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    # Optional SMTP (e.g. Gmail App Password for sending to any email address)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")


settings = Settings()
