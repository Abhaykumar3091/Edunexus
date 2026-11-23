import logging
import os
import ssl
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = logging.getLogger(__name__)


class Base(AsyncAttrs, DeclarativeBase):
    """
    SQLAlchemy 2.0 Base declarative class with AsyncAttrs support.
    """
    pass


# Primary database connection string (PostgreSQL via asyncpg or SQLite fallback)
connect_args = {}

raw_url = os.environ.get("DATABASE_URL", "").strip() or settings.DATABASE_URL
has_env_db = bool(os.environ.get("DATABASE_URL", "").strip())
use_sqlite = settings.USE_SQLITE_FALLBACK and not has_env_db

if use_sqlite:
    database_url = f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}"
    connect_args["check_same_thread"] = False
else:
    database_url = raw_url
    # Adapt Heroku postgres:// or postgresql:// to postgresql+asyncpg://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and not database_url.startswith("postgresql+asyncpg://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Asyncpg does not support sslmode in URL query params; configure SSL context for Heroku Postgres
    if "sslmode=" in database_url or os.environ.get("DYNO") or "heroku" in database_url:
        if "?" in database_url:
            base_url, query_str = database_url.split("?", 1)
            clean_params = [p for p in query_str.split("&") if not p.startswith("sslmode=")]
            database_url = base_url + (("?" + "&".join(clean_params)) if clean_params else "")
        ssl_ctx = ssl.create_default_context()
        ssl_ctx.check_hostname = False
        ssl_ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ssl_ctx

# Create the single unified asynchronous SQLAlchemy 2.0 engine
engine = create_async_engine(
    database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Create the sessionmaker for asynchronous sessions
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields an asynchronous database session
    and guarantees proper cleanup/rollback on error.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db_models():
    """
    Initialize database tables asynchronously.
    For production, Alembic migrations are used; this helper is for testing and dev bootstrap.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully.")
