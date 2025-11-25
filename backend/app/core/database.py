"""
Database configuration and session management.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings


# Create base class for models
Base = declarative_base()

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

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
