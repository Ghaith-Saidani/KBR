import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.models.event import EventStatus


class EventCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
        description="Event title.",
        examples=["KBR Community Meetup"],
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
        description="Optional event description.",
    )

    location: str | None = Field(
        default=None,
        max_length=255,
        description="Optional event location.",
    )

    start_at: datetime = Field(
        description="Event start date and time.",
    )

    end_at: datetime | None = Field(
        default=None,
        description="Optional event end date and time.",
    )

    cover_image: str | None = Field(
        default=None,
        max_length=500,
        description="Optional cover image URL.",
    )

    status: EventStatus = Field(
        default=EventStatus.DRAFT,
        description="Initial event status.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("title cannot be empty.")

        return value

    @field_validator(
        "description",
        "location",
        "cover_image",
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

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError(
                "end_at must be later than start_at."
            )

        return self


class EventUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated event title.",
    )

    description: str | None = Field(
        default=None,
        max_length=10000,
        description="Updated event description.",
    )

    location: str | None = Field(
        default=None,
        max_length=255,
        description="Updated event location.",
    )

    start_at: datetime | None = Field(
        default=None,
        description="Updated event start date and time.",
    )

    end_at: datetime | None = Field(
        default=None,
        description="Updated event end date and time.",
    )

    cover_image: str | None = Field(
        default=None,
        max_length=500,
        description="Updated cover image URL.",
    )

    status: EventStatus | None = Field(
        default=None,
        description="Updated event status.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("title cannot be empty.")

        return value

    @field_validator(
        "description",
        "location",
        "cover_image",
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

    @model_validator(mode="after")
    def validate_dates(self):
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at <= self.start_at
        ):
            raise ValueError(
                "end_at must be later than start_at."
            )

        return self


class EventResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    title: str
    description: str | None
    location: str | None
    start_at: datetime
    end_at: datetime | None
    cover_image: str | None
    status: EventStatus
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EventListResponse(BaseModel):
    items: list[EventResponse]
    total: int
    skip: int
    limit: int