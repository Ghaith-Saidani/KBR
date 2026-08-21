import uuid
from datetime import timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
)
from backend.app.models.member import Member
from backend.app.models.user import User, UserRole, UserStatus


def auth_headers(user: User) -> dict[str, str]:
    """Create Authorization headers for a test user."""

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    return {
        "Authorization": f"Bearer {token}",
    }


def create_test_user(
    db: Session,
    *,
    email: str = "test@example.com",
    password: str = "TestPassword123!",
    role: UserRole = UserRole.MEMBER,
    status: UserStatus = UserStatus.ACTIVE,
    is_email_verified: bool = True,
) -> User:
    """Create a user directly in the test database."""

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        status=status,
        is_email_verified=is_email_verified,
    )

    db.add(user)
    db.flush()

    return user


def test_register_user(
    client: TestClient,
    db: Session,
):
    response = client.post(
        "/auth/register",
        json={
            "email": "new-user@example.com",
            "password": "StrongPassword123!",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+21612345678",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "new-user@example.com"
    assert data["role"] == "member"
    assert data["status"] == "pending"
    assert data["is_email_verified"] is False
    assert "id" in data
    assert "created_at" in data

    user = db.query(User).filter(
        User.email == "new-user@example.com"
    ).first()

    assert user is not None
    assert user.password_hash != "StrongPassword123!"

    member = db.query(Member).filter(
        Member.user_id == user.id
    ).first()

    assert member is not None
    assert member.first_name == "John"
    assert member.last_name == "Doe"
    assert member.phone == "+21612345678"


def test_register_normalizes_email_and_names(
    client: TestClient,
    db: Session,
):
    response = client.post(
        "/auth/register",
        json={
            "email": "  USER@Example.COM  ",
            "password": "StrongPassword123!",
            "first_name": "  John  ",
            "last_name": "  Doe  ",
            "phone": "  +21612345678  ",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "user@example.com"

    user = db.query(User).filter(
        User.email == "user@example.com"
    ).first()

    assert user is not None

    member = db.query(Member).filter(
        Member.user_id == user.id
    ).first()

    assert member is not None
    assert member.first_name == "John"
    assert member.last_name == "Doe"
    assert member.phone == "+21612345678"


def test_register_duplicate_email_returns_409(
    client: TestClient,
    db: Session,
):
    create_test_user(
        db,
        email="existing@example.com",
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "existing@example.com",
            "password": "StrongPassword123!",
            "first_name": "Jane",
            "last_name": "Doe",
        },
    )

    assert response.status_code == 409

    data = response.json()

    assert "already exists" in data["detail"].lower()


def test_register_duplicate_email_is_case_insensitive(
    client: TestClient,
    db: Session,
):
    create_test_user(
        db,
        email="existing@example.com",
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "EXISTING@EXAMPLE.COM",
            "password": "StrongPassword123!",
            "first_name": "Jane",
            "last_name": "Doe",
        },
    )

    assert response.status_code == 409


def test_register_rejects_short_password(
    client: TestClient,
):
    response = client.post(
        "/auth/register",
        json={
            "email": "short@example.com",
            "password": "short",
            "first_name": "John",
            "last_name": "Doe",
        },
    )

    assert response.status_code == 422


def test_register_rejects_missing_required_fields(
    client: TestClient,
):
    response = client.post(
        "/auth/register",
        json={
            "email": "missing@example.com",
            "password": "StrongPassword123!",
        },
    )

    assert response.status_code == 422


def test_login_requires_valid_credentials(
    client: TestClient,
    db: Session,
):
    create_test_user(
        db,
        email="login@example.com",
        password="CorrectPassword123!",
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid email or password."


def test_pending_user_cannot_login(
    client: TestClient,
    db: Session,
):
    create_test_user(
        db,
        email="pending@example.com",
        password="CorrectPassword123!",
        status=UserStatus.PENDING,
        is_email_verified=False,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "pending@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 403

    data = response.json()

    assert "pending" in data["detail"].lower()


def test_suspended_user_cannot_login(
    client: TestClient,
    db: Session,
):
    create_test_user(
        db,
        email="suspended@example.com",
        password="CorrectPassword123!",
        status=UserStatus.SUSPENDED,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "suspended@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 403

    data = response.json()

    assert "suspended" in data["detail"].lower()


def test_login_returns_access_token(
    client: TestClient,
    db: Session,
):
    user = create_test_user(
        db,
        email="login@example.com",
        password="CorrectPassword123!",
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert len(data["access_token"]) > 20

    assert data["expires_in"] > 0

    assert data["user"]["id"] == str(user.id)
    assert data["user"]["email"] == "login@example.com"
    assert data["user"]["role"] == "member"
    assert data["user"]["status"] == "active"


def test_login_normalizes_email(
    client: TestClient,
    db: Session,
):
    create_test_user(
        db,
        email="login@example.com",
        password="CorrectPassword123!",
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "  LOGIN@EXAMPLE.COM  ",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 200


def test_login_token_contains_expected_claims(
    client: TestClient,
    db: Session,
):
    user = create_test_user(
        db,
        email="claims@example.com",
        password="CorrectPassword123!",
        role=UserRole.STAFF,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "claims@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    payload = decode_access_token(token)

    assert payload["sub"] == str(user.id)
    assert payload["role"] == "staff"
    assert payload["type"] == "access"
    assert "iat" in payload
    assert "exp" in payload
    assert payload["exp"] > payload["iat"]


def test_auth_me_requires_authentication(
    client: TestClient,
):
    response = client.get("/auth/me")

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Authentication required."


def test_auth_me_returns_current_user(
    client: TestClient,
    db: Session,
):
    user = create_test_user(
        db,
        email="me@example.com",
        password="CorrectPassword123!",
        role=UserRole.MEMBER,
    )

    response = client.get(
        "/auth/me",
        headers=auth_headers(user),
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["email"] == "me@example.com"
    assert data["role"] == "member"
    assert data["status"] == "active"
    assert data["is_email_verified"] is True


def test_auth_me_rejects_invalid_token(
    client: TestClient,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer definitely-not-a-valid-token",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid or expired access token."


def test_auth_me_rejects_wrong_authentication_scheme(
    client: TestClient,
):
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Basic abc123",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid authentication scheme."


def test_auth_me_rejects_token_with_wrong_type(
    client: TestClient,
    db: Session,
):
    user = create_test_user(db)

    settings = get_settings()

    token = jwt.encode(
        {
            "sub": str(user.id),
            "role": user.role.value,
            "type": "refresh",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid access token."


def test_auth_me_rejects_token_without_subject(
    client: TestClient,
    db: Session,
):
    user = create_test_user(db)

    settings = get_settings()

    token = jwt.encode(
        {
            "role": user.role.value,
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "Invalid access token."


def test_auth_me_rejects_deleted_user(
    client: TestClient,
    db: Session,
):
    user = create_test_user(db)

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    db.delete(user)
    db.flush()

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401

    data = response.json()

    assert data["detail"] == "User no longer exists."


def test_auth_me_rejects_suspended_user(
    client: TestClient,
    db: Session,
):
    user = create_test_user(
        db,
        status=UserStatus.SUSPENDED,
    )

    response = client.get(
        "/auth/me",
        headers=auth_headers(user),
    )

    assert response.status_code == 403

    data = response.json()

    assert "suspended" in data["detail"].lower()


def test_dev_activate_user(
    client: TestClient,
    db: Session,
):
    user = create_test_user(
        db,
        email="activate@example.com",
        status=UserStatus.PENDING,
        is_email_verified=False,
    )

    response = client.post(
        f"/auth/dev/activate/{user.id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(user.id)
    assert data["status"] == "active"


def test_dev_activate_missing_user_returns_404(
    client: TestClient,
):
    missing_id = uuid.uuid4()

    response = client.post(
        f"/auth/dev/activate/{missing_id}",
    )

    assert response.status_code == 404


def test_dev_activate_already_active_user_is_idempotent(
    client: TestClient,
    db: Session,
):
    user = create_test_user(
        db,
        status=UserStatus.ACTIVE,
    )

    response = client.post(
        f"/auth/dev/activate/{user.id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "active"


def test_dev_activate_suspended_user_is_rejected(
    client: TestClient,
    db: Session,
):
    user = create_test_user(
        db,
        status=UserStatus.SUSPENDED,
    )

    response = client.post(
        f"/auth/dev/activate/{user.id}",
    )

    assert response.status_code == 403

    data = response.json()

    assert "suspended" in data["detail"].lower()


def test_create_access_token_respects_custom_expiration(
    db: Session,
):
    user = create_test_user(db)

    token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        expires_delta=timedelta(seconds=60),
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user.id)
    assert payload["role"] == user.role.value
    assert payload["type"] == "access"
    assert payload["exp"] - payload["iat"] == 60