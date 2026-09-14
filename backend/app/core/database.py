"""
Database configuration and session management.
"""

from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)

# Create base class for models
Base = declarative_base()

# Create async engine with connection pooling configuration
# Pool settings optimized for typical web application workloads:
# - pool_size: Number of connections to maintain in the pool (default: 5)
# - max_overflow: Additional connections allowed above pool_size (default: 10)
# - pool_pre_ping: Verify connections before using them (prevents stale connections)
# Note: SQLite doesn't support connection pooling, so these params are only for PostgreSQL/MySQL
engine_kwargs = {
    "echo": settings.DEBUG,
    "future": True,
}

# Only add pool parameters for non-SQLite databases
if not settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_size": 5,  # Keep 5 persistent connections
            "max_overflow": 10,  # Allow up to 15 total connections (5 + 10)
            "pool_pre_ping": True,  # Verify connection health before use
        }
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_kwargs)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession]:
    """
    Dependency function that yields database sessions.

    Usage:
        @app.get("/items")
        async def read_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def _alembic_head() -> str | None:
    """
    Return the head revision defined in alembic/versions, or None if unavailable.

    Returns None rather than raising when the migration scripts aren't deployed
    alongside the app (e.g. the Cloudflare D1 build), so the revision comparison
    is skipped instead of blocking startup.
    """
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        backend_root = Path(__file__).resolve().parents[2]
        ini_path = backend_root / "alembic.ini"
        if not ini_path.exists():
            return None

        config = Config(str(ini_path))
        # script_location is relative in alembic.ini; resolve it so this works
        # regardless of the process working directory.
        config.set_main_option("script_location", str(backend_root / "alembic"))
        return ScriptDirectory.from_config(config).get_current_head()
    except Exception as e:
        logger.warning("alembic_head_lookup_failed", error=str(e))
        return None


async def init_db() -> None:
    """
    Verify the database schema is up to date.

    Alembic owns the schema (see alembic/versions/). Building tables from model
    metadata here would leave the database without a revision stamp, so a later
    `alembic upgrade head` would fail re-adding columns that already exist.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version"))
            current = result.scalar_one_or_none()
    except Exception as e:
        raise RuntimeError(
            "Database schema is not initialized. Run: uv run alembic upgrade head"
        ) from e

    expected = _alembic_head()
    if expected is not None and current != expected:
        raise RuntimeError(
            f"Database is at Alembic revision {current!r}, expected {expected!r}. "
            "Run: uv run alembic upgrade head"
        )

    logger.info("database_schema_verified", revision=current)


async def cleanup_expired_data(session: AsyncSession) -> int:
    """
    Clean up expired data from the database.

    Returns:
        Number of records deleted
    """
    from app.models.oauth_state import OAuthState

    deleted_count = await OAuthState.cleanup_expired(session)
    return deleted_count


async def close_db():
    """Close database connections."""
    await engine.dispose()
