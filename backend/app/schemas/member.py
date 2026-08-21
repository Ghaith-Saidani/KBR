from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MemberResponse(BaseModel):
    """
    Private member response.

    Used for the authenticated user's own profile.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    user_id: UUID

    first_name: str
    last_name: str

    phone: str | None
    profile_image: str | None
    bio: str | None
    joined_at: date | None

    created_at: datetime
    updated_at: datetime


class PublicMemberResponse(BaseModel):
    """
    Public member response.

    Sensitive/private fields such as phone and user_id
    are intentionally excluded.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID

    first_name: str
    last_name: str

    profile_image: str | None
    bio: str | None
    joined_at: date | None

    created_at: datetime


class MemberUpdateRequest(BaseModel):
    """
    Fields that an authenticated member can update.
    """

    first_name: str | None = Field(
        default=None,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
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
    def validate_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "Name cannot be empty."
            )

        return value

    @field_validator("phone", "profile_image", "bio")
    @classmethod
    def normalize_optional_string(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None