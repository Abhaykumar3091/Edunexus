import logging
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
if settings.USE_SQLITE_FALLBACK:
    database_url = f"sqlite+aiosqlite:///{settings.SQLITE_DB_PATH}"
    connect_args["check_same_thread"] = False
else:
    database_url = settings.DATABASE_URL

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
