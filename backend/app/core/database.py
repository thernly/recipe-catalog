"""
Database configuration and session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings


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


async def get_db() -> AsyncGenerator[AsyncSession, None]:
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


async def init_db():
    """Initialize database tables."""
    # Import all models to ensure they're registered with SQLAlchemy
    from app.models import (  # noqa: F401
        Collection,
        Household,
        HouseholdInvitation,
        HouseholdMember,
        PasswordResetToken,
        Recipe,
        RecipeCollection,
        ShoppingList,
        ShoppingListItem,
        User,
        UserPreferences,
        VerificationToken,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
