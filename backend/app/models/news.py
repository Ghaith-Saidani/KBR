import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, TimestampMixin
from backend.app.models.user import User


class NewsStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class News(Base, TimestampMixin):
    __tablename__ = "news"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(220),
        unique=True,
        nullable=False,
        index=True,
    )

    excerpt: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    cover_image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    status: Mapped[NewsStatus] = mapped_column(
        Enum(NewsStatus, name="news_status"),
        default=NewsStatus.DRAFT,
        nullable=False,
        index=True,
    )

    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    creator: Mapped[User] = relationship(
        "User",
        foreign_keys=[created_by],
    )