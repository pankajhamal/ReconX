"""Database connection and session."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    """Parent class for all database tables."""


def get_db():
    """Give one database session per API request, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables that don't exist yet."""
    import app.models  # noqa: F401  (registers the tables on Base)

    Base.metadata.create_all(bind=engine)
