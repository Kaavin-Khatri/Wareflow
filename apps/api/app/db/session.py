"""
Database engine and session management.

Configured with NullPool for Supabase connection pooler (Supavisor) compatibility:
1. NullPool: Supabase pools connections server-side via Supavisor (port 6543).
   Client-side pooling causes double-pooling and exhausted connection limits.
   NullPool opens connections on demand and returns them immediately.
2. pool_pre_ping=True: Tests connections before checkout to transparently recover
   from cloud network drops or idle timeouts.
"""

from collections.abc import Generator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


def normalize_database_url(url: str) -> str:
    """Normalize Postgres connection URL scheme for psycopg driver."""
    if not url:
        return ""
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@lru_cache
def get_engine() -> Engine:
    """
    Create and cache the SQLAlchemy Engine.

    Uses DATABASE_URL (runtime pooler connection) with NullPool.
    """
    settings = get_settings()
    db_url = normalize_database_url(settings.database_url)

    if not db_url:
        # Fallback to local SQLite in-memory for testing if no DB URL is set
        return create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
        )

    return create_engine(
        db_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )


def get_session_factory() -> sessionmaker[Session]:
    """Get the sessionmaker factory bound to the active engine."""
    engine = get_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a transactional database session.

    Ensures the session is cleanly closed after the request completes.
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
