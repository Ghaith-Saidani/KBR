import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from backend.app.models.user import UserRole, UserStatus


class AdminMemberResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    user_id: uuid.UUID
    member_id: uuid.UUID

    email: EmailStr

    first_name: str
    last_name: str

    phone: str | None
    profile_image: str | None
    bio: str | None
    joined_at: date | None

    role: UserRole
    status: UserStatus
    is_email_verified: bool

    created_at: datetime
    updated_at: datetime


class AdminMemberUpdateRequest(BaseModel):
    first_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        min_length=1,
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


class AdminRoleUpdateRequest(BaseModel):
    role: UserRole


class AdminMemberListResponse(BaseModel):
    items: list[AdminMemberResponse]
    total: int