from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserActivityResponse(BaseModel):
    """Represent a single user activity log."""

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    user_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: UUID | None
    method: str | None
    endpoint: str | None
    ip_address: str | None
    user_agent: str | None
    details: str | None
    activity_metadata: dict[str, object] | None
    occurred_at: datetime
    created_at: datetime
    updated_at: datetime


class UserActivityListResponse(BaseModel):
    """Paginated activity-log response."""

    items: list[UserActivityResponse]
    total: int
    page: int
    page_size: int
    pages: int