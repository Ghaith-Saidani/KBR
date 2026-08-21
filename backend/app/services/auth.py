from datetime import date

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.security import (
    hash_password,
    verify_password_with_dummy,
)
from backend.app.models.member import Member
from backend.app.models.user import User
from backend.app.schemas.auth import RegisterRequest
from backend.app.services.member import generate_unique_slug


class AuthError(Exception):
    """Base authentication service error."""


class EmailAlreadyExistsError(AuthError):
    """Raised when an email is already registered."""


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid."""


class InactiveUserError(AuthError):
    """Raised when a user cannot authenticate because of their status."""


def normalize_email(email: str) -> str:
    """Normalize an email address before storing/searching it."""

    return email.strip().lower()


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    """Find a user by normalized email."""

    normalized_email = normalize_email(email)

    statement = select(User).where(
        User.email == normalized_email
    )

    return db.scalar(statement)


def register_user(
    db: Session,
    data: RegisterRequest,
) -> User:
    """Create a user and their member profile."""

    email = normalize_email(data.email)

    existing_user = get_user_by_email(
        db,
        email,
    )

    if existing_user is not None:
        raise EmailAlreadyExistsError(
            "An account with this email already exists."
        )

    first_name = data.first_name.strip()
    last_name = data.last_name.strip()

    user = User(
        email=email,
        password_hash=hash_password(
            data.password
        ),
    )

    db.add(user)

    try:
        db.flush()

    except IntegrityError:
        db.rollback()

        raise EmailAlreadyExistsError(
            "An account with this email already exists."
        )

    member = Member(
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        slug=generate_unique_slug(
            db,
            first_name,
            last_name,
        ),
        phone=(
            data.phone.strip()
            if data.phone
            else None
        ),
        joined_at=date.today(),
    )

    db.add(member)

    try:
        db.commit()

    except IntegrityError:
        db.rollback()

        raise EmailAlreadyExistsError(
            "Unable to create the account."
        )

    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User:
    """Authenticate a user using email and password."""

    user = get_user_by_email(
        db,
        email,
    )

    hashed_password = (
        user.password_hash
        if user is not None
        else None
    )

    password_valid = verify_password_with_dummy(
        password,
        hashed_password,
    )

    if user is None or not password_valid:
        raise InvalidCredentialsError(
            "Invalid email or password."
        )

    if user.status.value == "suspended":
        raise InactiveUserError(
            "This account has been suspended."
        )

    if user.status.value == "pending":
        raise InactiveUserError(
            "This account is still pending activation."
        )

    return user