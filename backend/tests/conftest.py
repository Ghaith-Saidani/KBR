import uuid
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.main import app
from backend.app.models.base import Base
from backend.app.models.user import User, UserRole, UserStatus


settings = get_settings()

TEST_DATABASE_URL = settings.database_url

test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    class_=Session,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """
    Provide an isolated database session for each test.

    The application is allowed to call session.commit(), while
    the outer transaction remains active and is rolled back after
    the test finishes.
    """

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(
        session: Session,
        transaction_obj,
    ) -> None:
        """
        Restart the nested SAVEPOINT after the application commits.

        This allows application code to use db.commit() normally
        without leaking test data into the real test database.
        """

        if transaction_obj.nested and not transaction_obj._parent.nested:
            session.begin_nested()

    try:
        yield session

    finally:
        event.remove(
            session,
            "after_transaction_end",
            restart_savepoint,
        )

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

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


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