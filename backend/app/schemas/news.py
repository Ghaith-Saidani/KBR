import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.app.models.news import NewsStatus


class NewsCreateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200,
        description="News article title.",
        examples=["KBR launches a new community initiative"],
    )

    slug: str = Field(
        min_length=1,
        max_length=220,
        description="Unique URL-friendly article slug.",
        examples=["kbr-launches-new-community-initiative"],
    )

    excerpt: str | None = Field(
        default=None,
        max_length=500,
        description="Optional short article summary.",
    )

    content: str = Field(
        min_length=1,
        description="Full news article content.",
    )

    cover_image: str | None = Field(
        default=None,
        max_length=500,
        description="Optional cover image URL.",
    )

    status: NewsStatus = Field(
        default=NewsStatus.DRAFT,
        description="Initial article status.",
    )

    published_at: datetime | None = Field(
        default=None,
        description="Publication date and time.",
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("title cannot be empty.")

        return value

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        value = value.strip().lower()

        if not value:
            raise ValueError("slug cannot be empty.")

        if " " in value:
            raise ValueError(
                "slug must not contain spaces."
            )

        return value

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("content cannot be empty.")

        return value

    @field_validator(
        "excerpt",
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
    def validate_publication(self):
        if (
            self.status == NewsStatus.PUBLISHED
            and self.published_at is None
        ):
            self.published_at = datetime.now().astimezone()

        return self


class NewsUpdateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="Updated article title.",
    )

    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=220,
        description="Updated unique article slug.",
    )

    excerpt: str | None = Field(
        default=None,
        max_length=500,
        description="Updated article summary.",
    )

    content: str | None = Field(
        default=None,
        min_length=1,
        description="Updated article content.",
    )

    cover_image: str | None = Field(
        default=None,
        max_length=500,
        description="Updated cover image URL.",
    )

    status: NewsStatus | None = Field(
        default=None,
        description="Updated article status.",
    )

    published_at: datetime | None = Field(
        default=None,
        description="Updated publication date and time.",
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
            raise ValueError("slug cannot be empty.")

        if " " in value:
            raise ValueError(
                "slug must not contain spaces."
            )

        return value

    @field_validator("content")
    @classmethod
    def validate_content(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        if not value:
            raise ValueError("content cannot be empty.")

        return value

    @field_validator(
        "excerpt",
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


class NewsResponse(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    title: str
    slug: str
    excerpt: str | None
    content: str
    cover_image: str | None
    status: NewsStatus
    published_at: datetime | None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class NewsListResponse(BaseModel):
    items: list[NewsResponse]
    total: int
    skip: int
    limit: int