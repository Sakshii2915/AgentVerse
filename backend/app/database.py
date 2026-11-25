"""Database connection and session management for AgentVerse."""

import logging
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import OperationalError
from app.config import settings

logger = logging.getLogger("agentverse.database")

Base = declarative_base()


def get_engine(db_url: str):
    """Create SQLAlchemy engine with appropriate connect args."""
    if db_url.startswith("sqlite"):
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=False
    )


# Primary engine initialization with graceful fallback to SQLite
db_url = settings.DATABASE_URL
try:
    engine = get_engine(db_url)
    # Test connection
    with engine.connect() as conn:
        pass
    logger.info("Connected successfully to primary database: %s", db_url.split("@")[-1] if "@" in db_url else db_url)
except (OperationalError, Exception) as exc:
    if not db_url.startswith("sqlite"):
        logger.warning(
            "Could not connect to PostgreSQL at %s (%s). Falling back to local SQLite at sqlite:///./agentverse.db",
            db_url,
            exc
        )
        db_url = "sqlite:///./agentverse.db"
        engine = get_engine(db_url)
    else:
        raise exc

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables on application startup."""
    import app.models.models  # Ensure models are registered with Base
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
