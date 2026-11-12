"""Async SQLAlchemy 2.0 engine, session factory and declarative Base (MySQL)."""

from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


def _async_url(url: str) -> str:
    """Convert a sync MySQL URL (e.g. mysql+pymysql) to the aiomysql async driver."""
    parsed = make_url(url)
    if parsed.get_backend_name() == "mysql":
        parsed = parsed.set(drivername="mysql+aiomysql")
    return parsed.render_as_string(hide_password=False)


engine = create_async_engine(
    _async_url(settings.database_url),
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


def utcnow() -> datetime:
    """Current UTC time as a naive datetime (stored in MySQL DATETIME columns, always UTC)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables registered on Base.metadata (models must be imported first)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the engine's connection pool."""
    await engine.dispose()
