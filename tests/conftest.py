"""
Test fixtures: test database, async client, and pre-authenticated users.

Uses a single shared connection with nested transactions so that
test-created data is visible to the dependency-injected sessions.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncConnection,
)

from app.database import Base
from app.dependencies.database import get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.auth_service import hash_password, create_access_token

# In-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@pytest_asyncio.fixture
async def db_connection():
    """
    Create a single connection and set up schema.
    All sessions in a test share this connection so in-memory SQLite works.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    conn = await test_engine.connect()
    try:
        yield conn
    finally:
        await conn.close()
        # Drop tables after test
        async with test_engine.begin() as conn2:
            await conn2.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(db_connection: AsyncConnection):
    """
    Provide a session bound to the shared connection.
    Uses a savepoint so we can rollback after each test.
    """
    # Start a transaction on the connection
    trans = await db_connection.begin()
    session = AsyncSession(bind=db_connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        if trans.is_active:
            await trans.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, db_connection: AsyncConnection):
    """Provide an async test client with test database."""

    async def override_get_db():
        """
        Yield the same session so the app sees test-created data.
        We do NOT commit/rollback here — the db_session fixture manages that.
        """
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for testing."""
    user = User(
        email="testadmin@test.com",
        username="testadmin",
        hashed_password=hash_password("admin123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def analyst_user(db_session: AsyncSession) -> User:
    """Create an analyst user for testing."""
    user = User(
        email="testanalyst@test.com",
        username="testanalyst",
        hashed_password=hash_password("analyst123"),
        full_name="Test Analyst",
        role=UserRole.ANALYST,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def viewer_user(db_session: AsyncSession) -> User:
    """Create a viewer user for testing."""
    user = User(
        email="testviewer@test.com",
        username="testviewer",
        hashed_password=hash_password("viewer123"),
        full_name="Test Viewer",
        role=UserRole.VIEWER,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


def get_auth_headers(user: User) -> dict:
    """Generate authorization headers for a user."""
    token = create_access_token(
        {"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return {"Authorization": f"Bearer {token}"}
