import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.permissions import require_admin
from backend.app.models.user import User
from backend.app.schemas.user_activity import (
    UserActivityListResponse,
)
from backend.app.services.user_activity import (
    list_user_activities,
)


router = APIRouter(
    prefix="/admin/activity-logs",
    tags=["admin activity logs"],
)


@router.get(
    "",
    response_model=UserActivityListResponse,
)
def get_activity_logs(
    page: int = Query(
        default=1,
        ge=1,
        description="Page number.",
    ),
    page_size: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of activity logs to return.",
    ),
    user_id: uuid.UUID | None = Query(
        default=None,
        description="Filter activity logs by user ID.",
    ),
    action: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Filter activity logs by action.",
    ),
    resource_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Filter activity logs by resource type.",
    ),
    method: str | None = Query(
        default=None,
        min_length=1,
        max_length=10,
        description="Filter activity logs by HTTP method.",
    ),
    date_from: datetime | None = Query(
        default=None,
        description="Return activity logs occurring at or after this timestamp.",
    ),
    date_to: datetime | None = Query(
        default=None,
        description="Return activity logs occurring at or before this timestamp.",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
        description="Sort activity logs by occurrence time.",
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> UserActivityListResponse:
    """List and filter user activity logs."""

    return list_user_activities(
        db,
        page=page,
        page_size=page_size,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        method=method,
        date_from=date_from,
        date_to=date_to,
        sort_order=sort_order,
    )