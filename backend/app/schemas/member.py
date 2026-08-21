from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.member import MemberStatus


class MemberBaseFields(BaseModel):
    first_name: str = Field(
        min_length=2,
        max_length=100,
    )

    last_name: str = Field(
        min_length=2,
        max_length=100,
    )

    position: str | None = Field(
        default=None,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    profile_image: str | None = Field(
        default=None,
        max_length=500,
    )

    bio: str | None = Field(
        default=None,
        max_length=2000,
    )

    joined_at: date | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        return value

    @field_validator(
        "position",
        "phone",
        "profile_image",
        "bio",
    )
    @classmethod
    def normalize_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class MemberResponse(BaseModel):
    """
    Private response for the authenticated member.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    user_id: UUID

    first_name: str
    last_name: str
    slug: str
    position: str | None

    phone: str | None
    profile_image: str | None
    bio: str | None
    joined_at: date | None

    status: MemberStatus

    created_at: datetime
    updated_at: datetime


class PublicMemberResponse(BaseModel):
    """
    Public member profile.

    Private account information is intentionally excluded.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    first_name: str
    last_name: str
    slug: str
    position: str | None

    profile_image: str | None
    bio: str | None
    joined_at: date | None

    status: MemberStatus

    created_at: datetime


class MemberUpdateRequest(BaseModel):
    """
    Member self-service update request.
    """

    first_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    position: str | None = Field(
        default=None,
        max_length=150,
    )

    phone: str | None = Field(
        default=None,
        max_length=30,
    )

    profile_image: str | None = Field(
        default=None,
        max_length=500,
    )

    bio: str | None = Field(
        default=None,
        max_length=2000,
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_names(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        return value

    @field_validator(
        "position",
        "phone",
        "profile_image",
        "bio",
    )
    @classmethod
    def normalize_optional_strings(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None


class MemberAdminUpdateRequest(MemberUpdateRequest):
    """
    Staff/admin update request.

    Staff and administrators can additionally control
    membership status.
    """

    status: MemberStatus | None = None


class MemberListResponse(BaseModel):
    """
    Paginated member collection.
    """

    items: list[PublicMemberResponse]
    total: int
    skip: int
    limit: int
