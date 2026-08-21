import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from backend.app.models.notification import NotificationType


class NotificationResponse(BaseModel):
    """Public representation of a notification."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    user_id: uuid.UUID
    type: NotificationType
    title: str
    message: str
    is_read: bool
    read_at: datetime | None
    created_at: datetime
    updated_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated notification list."""

    items: list[NotificationResponse]
    total: int
    skip: int
    limit: int
    unread_count: int


class NotificationUnreadCountResponse(BaseModel):
    """Unread notification count."""

    unread_count: int


class NotificationReadResponse(BaseModel):
    """Response returned after marking a notification as read."""

    message: str
    notification: NotificationResponse


class NotificationReadAllResponse(BaseModel):
    """Response returned after marking all notifications as read."""

    message: str
    updated_count: int
