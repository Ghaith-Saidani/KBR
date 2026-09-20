import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.user import User, UserRole, UserStatus

from backend.app.middleware.activity_logging import (
    ActivityLoggingMiddleware,
)

settings = get_settings()

TEST_DATABASE_URL = settings.test_database_url

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
    join_transaction_mode="create_savepoint",
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> None:
    """
    Prepare the dedicated test database.

    The test database is completely separate from the development
    database and receives the current SQLAlchemy schema before tests run.
    """

    Base.metadata.create_all(
        bind=test_engine,
    )

    yield

    Base.metadata.drop_all(
        bind=test_engine,
    )


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Provide an isolated database session for each test.

    A real outer transaction is opened on the connection. The SQLAlchemy
    session uses create_savepoint mode so application code can freely call
    session.commit() without committing the outer test transaction.

    At the end of the test, the outer transaction is rolled back,
    guaranteeing that database changes do not leak into another test.
    """

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
    )

    try:
        yield session

    finally:
        session.close()

        if transaction.is_active:
            transaction.rollback()

        connection.close()


@pytest.fixture
def client(
    db: Session,
) -> Generator[TestClient, None, None]:
    """
    Provide a FastAPI test client using the test database session.
    """

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    setattr(
        app.state,
        ActivityLoggingMiddleware.SESSION_STATE_KEY,
        db,
    )

    try:
        with TestClient(app) as test_client:
            yield test_client

    finally:
        app.dependency_overrides.clear()

        if hasattr(
            app.state,
            ActivityLoggingMiddleware.SESSION_STATE_KEY,
        ):
            delattr(
                app.state,
                ActivityLoggingMiddleware.SESSION_STATE_KEY,
            )


def create_test_user(
    db: Session,
    *,
    role: UserRole = UserRole.MEMBER,
    status: UserStatus = UserStatus.ACTIVE,
    email: str | None = None,
) -> User:
    """
    Create a test user directly in the database.
    """

    user = User(
        id=uuid.uuid4(),
        email=email or f"test-{uuid.uuid4()}@example.com",
        password_hash="test-password-hash",
        role=role,
        status=status,
        is_email_verified=True,
    )

    db.add(user)
    db.flush()

    return user


@pytest.fixture
def member_user(db: Session) -> User:
    return create_test_user(
        db,
        role=UserRole.MEMBER,
    )


@pytest.fixture
def staff_user(db: Session) -> User:
    return create_test_user(
        db,
        role=UserRole.STAFF,
    )


@pytest.fixture
def admin_user(db: Session) -> User:
    return create_test_user(
        db,
        role=UserRole.ADMIN,
    )