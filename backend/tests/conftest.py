"""Pytest configuration and fixtures."""

import os


# Set required environment variables before importing app modules
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-min-32-characters-long")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost:5173")
os.environ.setdefault("ALLOWED_METHODS", "GET,POST,PUT,DELETE,PATCH")
os.environ.setdefault("ALLOWED_HEADERS", "Authorization,Content-Type,Accept,X-CSRF-Token")
os.environ.setdefault("ALLOWED_IMAGE_TYPES", "image/jpeg,image/png,image/webp")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.main import app
from app.models.household import Household, HouseholdMember
from app.models.user import User


# Test database URL - use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session", autouse=True)
def enable_testing_mode():
    """Enable testing mode to disable rate limiting for all tests."""
    original_env = settings.ENVIRONMENT
    settings.ENVIRONMENT = "testing"
    settings.TESTING = True
    yield
    settings.TESTING = False
    settings.ENVIRONMENT = original_env


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Clean up
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db(test_engine):
    """Create test database session."""
    AsyncTestSession = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    async with AsyncTestSession() as session:
        yield session


@pytest_asyncio.fixture
async def test_user(test_db):
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True,
        display_name="Test User",
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def db(test_db):
    """Alias for test_db to match test expectations."""
    return test_db


@pytest_asyncio.fixture
async def client(test_db):
    """Create test client with database override."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_headers(client: AsyncClient):
    """Create a test user and return authorization headers."""
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "SecurePass123!",
            "display_name": "Test User",
        },
    )

    # Login to get token cookie
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "SecurePass123!"},
    )

    # Extract token from cookies
    token = login_response.cookies.get("access_token")
    csrf_token = login_response.cookies.get("csrf_token")

    headers = {"Authorization": f"Bearer {token}"}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token

    return headers


@pytest_asyncio.fixture
async def test_household(db: AsyncSession, test_user: User):
    """Create a test household for test_user."""
    household = Household(
        name="Test Household",
        owner_user_id=test_user.id,
        max_members=10,
    )
    db.add(household)
    await db.commit()
    await db.refresh(household)

    # Add user as household member
    member = HouseholdMember(
        household_id=household.id,
        user_id=test_user.id,
        role="owner",
    )
    db.add(member)
    await db.commit()

    # Return dict format for compatibility with existing tests
    return {
        "id": household.id,
        "name": household.name,
        "owner_user_id": household.owner_user_id,
    }


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user: User, test_household: dict):
    """Create auth headers for the test_user fixture."""
    # Login with the test_user credentials
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpassword"},
    )

    if login_response.status_code != 200:
        return {}

    # Extract token from cookies
    token = login_response.cookies.get("access_token")
    csrf_token = login_response.cookies.get("csrf_token")

    headers = {"Authorization": f"Bearer {token}"}
    if csrf_token:
        headers["X-CSRF-Token"] = csrf_token

    return headers
