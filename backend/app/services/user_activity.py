import math
import uuid
from collections.abc import Mapping
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.user_activity import UserActivity
from backend.app.schemas.user_activity import (
    UserActivityListResponse,
)


def log_user_activity(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    method: str | None = None,
    endpoint: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    details: str | None = None,
    activity_metadata: Mapping[str, object] | None = None,
    occurred_at: datetime | None = None,
) -> UserActivity:
    """
    Record a user activity in the current database transaction.

    The function intentionally does not commit the transaction.
    The caller remains responsible for committing or rolling back.
    """

    activity = UserActivity(
        id=uuid.uuid4(),
        user_id=user_id,
        action=action.strip(),
        resource_type=(
            resource_type.strip()
            if resource_type
            else None
        ),
        resource_id=resource_id,
        method=(
            method.strip().upper()
            if method
            else None
        ),
        endpoint=(
            endpoint.strip()
            if endpoint
            else None
        ),
        ip_address=(
            ip_address.strip()
            if ip_address
            else None
        ),
        user_agent=(
            user_agent.strip()
            if user_agent
            else None
        ),
        details=(
            details.strip()
            if details
            else None
        ),
        activity_metadata=(
            dict(activity_metadata)
            if activity_metadata is not None
            else None
        ),
    )

    if occurred_at is not None:
        activity.occurred_at = occurred_at

    db.add(activity)
    db.flush()

    return activity


def list_user_activities(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 50,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    method: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_order: str = "desc",
) -> UserActivityListResponse:
    """
    Return a paginated list of user activity logs.

    Supports filtering by user, action, resource type,
    HTTP method, and occurrence date range.
    """

    filters = []

    if user_id is not None:
        filters.append(
            UserActivity.user_id == user_id
        )

    if action:
        filters.append(
            UserActivity.action == action.strip()
        )

    if resource_type:
        filters.append(
            UserActivity.resource_type
            == resource_type.strip()
        )

    if method:
        filters.append(
            UserActivity.method
            == method.strip().upper()
        )

    if date_from is not None:
        filters.append(
            UserActivity.occurred_at >= date_from
        )

    if date_to is not None:
        filters.append(
            UserActivity.occurred_at <= date_to
        )

    total = (
        db.scalar(
            select(func.count(UserActivity.id))
            .where(*filters)
        )
        or 0
    )

    if sort_order.lower() == "asc":
        order_column = (
            UserActivity.occurred_at.asc()
        )
    else:
        order_column = (
            UserActivity.occurred_at.desc()
        )

    offset = (page - 1) * page_size

    statement = (
        select(UserActivity)
        .where(*filters)
        .order_by(order_column)
        .offset(offset)
        .limit(page_size)
    )

    items = list(
        db.scalars(statement).all()
    )

    pages = (
        math.ceil(total / page_size)
        if total > 0
        else 0
    )

    return UserActivityListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )