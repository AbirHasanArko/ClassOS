"""
ClassOS — Database Connection
Async SQLAlchemy engine and session factory using asyncpg.
Connection pooling tuned for Raspberry Pi 5.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import settings

# Create async engine with connection pooling
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_pre_ping=True,       # Verify connections before use
    pool_recycle=3600,         # Recycle connections after 1 hour
    echo=settings.DEBUG,       # Log SQL in debug mode
)

# Session factory — produces AsyncSession instances
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Don't expire objects after commit
)
