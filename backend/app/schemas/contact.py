import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from backend.app.models.contact import ContactMessageStatus


class ContactMessageCreateRequest(BaseModel):
    """
    Public request for submitting a contact message.
    """

    name: str = Field(
        min_length=2,
        max_length=150,
    )

    email: EmailStr

    subject: str = Field(
        min_length=3,
        max_length=200,
    )

    message: str = Field(
        min_length=10,
        max_length=10_000,
    )

    @field_validator("name", "subject", "message")
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Field cannot be empty.")

        return value


class ContactMessageUpdateRequest(BaseModel):
    """
    Staff/admin request for updating a contact message.
    """

    status: ContactMessageStatus


class ContactMessageResponse(BaseModel):
    """
    Contact message returned by the API.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    name: str
    email: EmailStr
    subject: str
    message: str
    status: ContactMessageStatus
    user_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ContactMessageListResponse(BaseModel):
    """
    Paginated contact message response.
    """

    items: list[ContactMessageResponse]
    total: int
    skip: int
    limit: int