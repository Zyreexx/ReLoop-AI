"""
Database engine, sessionmaker, and FastAPI get_db dependency.
Supports PostgreSQL (default per architecture) with automatic SQLite fallback for lightweight testing/local setup.
"""
import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.db.base import Base

logger = logging.getLogger(__name__)


def _create_database_engine():
    connect_args = {}
    if settings.DATABASE_URL.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    try:
        eng = create_engine(
            settings.DATABASE_URL,
            connect_args=connect_args,
            pool_pre_ping=True,
        )
        # Test connection
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Connected to database successfully.")
        return eng
    except Exception:
        logger.warning("Could not connect to primary database. Falling back to local SQLite './reloop.db'.")
        return create_engine(
            "sqlite:///./reloop.db",
            connect_args={"check_same_thread": False},
        )


engine = _create_database_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_all_tables():
    """
    Initializes all database tables registered with Base metadata.
    """
    global engine, SessionLocal
    import app.models.entities  # Ensure all model tables are registered
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.warning(f"create_all_tables failed on current engine: {e}. Retrying with SQLite...")
        engine = create_engine(
            "sqlite:///./reloop.db",
            connect_args={"check_same_thread": False},
        )
        SessionLocal.configure(bind=engine)
        Base.metadata.create_all(bind=engine)
