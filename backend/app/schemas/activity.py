import uuid
from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from backend.app.models.activity import ActivityStatus


class ActivityCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
    )

    slug: str = Field(
        min_length=1,
        max_length=220,
    )

    excerpt: str | None = Field(
        default=None,
        max_length=500,
    )

    description: str = Field(
        min_length=1,
    )

    cover_image: str | None = Field(
        default=None,
        max_length=500,
    )

    status: ActivityStatus = Field(
        default=ActivityStatus.DRAFT,
    )

    start_at: datetime | None = None

    end_at: datetime | None = None

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    published_at: datetime | None = None


    @field_validator("title")
    @classmethod
    def validate_title(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "title cannot be empty.",
            )

        return value


    @field_validator("slug")
    @classmethod
    def validate_slug(
        cls,
        value: str,
    ) -> str:
        value = value.strip().lower()

        if not value:
            raise ValueError(
                "slug cannot be empty.",
            )

        if " " in value:
            raise ValueError(
                "slug must not contain spaces.",
            )

        return value


    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str,
    ) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "description cannot be empty.",
            )

        return value


    @field_validator(
        "excerpt",
        "cover_image",
        "location",
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
    def validate_dates_and_publication(
        self,
    ):
        if (
            self.start_at is not None
            and self.end_at is not None
            and self.end_at < self.start_at
        ):
            raise ValueError(
                "end_at cannot be earlier than start_at.",
            )

        if self.status == ActivityStatus.PUBLISHED:
            if self.published_at is None:
                self.published_at = (
                    datetime.now().astimezone()
                )

        elif self.status == ActivityStatus.DRAFT:
            self.published_at = None

        return self


class ActivityUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=220,
    )

    excerpt: str | None = Field(
        default=None,
        max_length=500,
    )

    description: str | None = Field(
        default=None,
        min_length=1,
    )

    cover_image: str | None = Field(
        default=None,
        max_length=500,
    )

    status: ActivityStatus | None = None

    start_at: datetime | None = None

    end_at: datetime | None = None

    location: str | None = Field(
        default=None,
        max_length=255,
    )

    published_at: datetime | None = None


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
            raise ValueError(
                "title cannot be empty.",
            )

        return value


    @field_validator("slug")
    @classmethod
    def validate_slug(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip().lower()

        if not value:
            raise ValueError(
                "slug cannot be empty.",
            )

        if " " in value:
            raise ValueError(
                "slug must not contain spaces.",
            )

        return value


    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError(
                "description cannot be empty.",
            )

        return value


    @field_validator(
        "excerpt",
        "cover_image",
        "location",
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
            and self.end_at < self.start_at
        ):
            raise ValueError(
                "end_at cannot be earlier than start_at.",
            )

        return self


class ActivityResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    title: str
    slug: str
    excerpt: str | None
    description: str
    cover_image: str | None
    status: ActivityStatus
    start_at: datetime | None
    end_at: datetime | None
    location: str | None
    published_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class ActivityListResponse(BaseModel):
    items: list[ActivityResponse]
    total: int
    skip: int
    limit: int