"""SQLAlchemy engine/session setup for Postgres."""
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.models import Base


@lru_cache
def get_engine():
    """Lazily created engine — avoids import-time failures when POSTGRES_URL is unset."""
    return create_engine(settings.postgres_url, pool_pre_ping=True)


def SessionLocal():
    """Session factory. A regular function so tests can monkeypatch it easily."""
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)()


def init_db():
    """Create all tables (fine for prototyping; swap for Alembic later)."""
    Base.metadata.create_all(bind=get_engine())


def get_db():
    """FastAPI dependency yielding a session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
