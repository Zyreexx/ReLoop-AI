"""
Configuration settings for ReLoop AI Backend.
"""
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base backend directory reference
BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_SQLITE_PATH = BACKEND_DIR / "reloop.db"

# Load backend/.env and root .env so configurations in either location are resolved
backend_env = BACKEND_DIR / ".env"
root_env = BACKEND_DIR.parent / ".env"
if root_env.exists():
    load_dotenv(root_env, override=True)
if backend_env.exists():
    load_dotenv(backend_env, override=True)
load_dotenv()

raw_db_url = os.getenv("DATABASE_URL", "").strip()
if not raw_db_url or raw_db_url in ("sqlite:///./reloop.db", "sqlite:///reloop.db"):
    resolved_db_url = f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
else:
    resolved_db_url = raw_db_url


class Settings:
    PROJECT_NAME: str = "ReLoop AI"
    VERSION: str = "0.1.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    MAX_UPLOAD_MB: int = 10
    DATABASE_URL: str = resolved_db_url
    DEFAULT_SQLITE_PATH: Path = DEFAULT_SQLITE_PATH

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
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_MEDIA_RESOLUTION: str = os.getenv("GEMINI_MEDIA_RESOLUTION", "HIGH")
    MAX_IDENTIFY_IMAGES: int = int(os.getenv("MAX_IDENTIFY_IMAGES", "5"))

    # Groq (Secondary fallback for vision)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.2-11b-vision-preview")

    # Fallback mode for demo deployment / Gemini failure (permanently disabled)
    DEMO_FALLBACK: bool = False

    # Resend
    RESEND_API_KEY: str = os.getenv("RESEND_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "onboarding@resend.dev")

    # Optional SMTP (e.g. Gmail App Password for sending to any email address)
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASS: str = os.getenv("SMTP_PASS", "")


settings = Settings()
