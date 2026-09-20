import math
import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.user_activity import UserActivity
from backend.app.schemas.user_activity import (
    UserActivityListResponse,
)
from backend.app.services.activity_logger import (
    log_user_activity,
)


BUSINESS_AUTH_ACTIONS = (
    "LOGIN",
    "REGISTER",
    "USER_ACTIVATED",
)

ActivityType = Literal[
    "business",
    "technical",
]


def list_user_activities(
    db: Session,
    *,
    page: int = 1,
    page_size: int = 50,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    resource_type: str | None = None,
    method: str | None = None,
    activity_type: ActivityType | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    sort_order: str = "desc",
) -> UserActivityListResponse:
    """
    Return a paginated list of user activity logs.

    Supports filtering by user, action, resource type,
    HTTP method, activity type, and occurrence date range.
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

    if activity_type == "business":
        filters.append(
            (
                UserActivity.action.like("MEMBER_%")
                | UserActivity.action.like("EVENT_%")
                | UserActivity.action.like("NEWS_%")
                | UserActivity.action.like("ACTIVITY_%")
                | UserActivity.action.in_(
                    BUSINESS_AUTH_ACTIONS
                )
            )
        )

    elif activity_type == "technical":
        filters.append(
            ~(
                UserActivity.action.like("MEMBER_%")
                | UserActivity.action.like("EVENT_%")
                | UserActivity.action.like("NEWS_%")
                | UserActivity.action.like("ACTIVITY_%")
                | UserActivity.action.in_(
                    BUSINESS_AUTH_ACTIONS
                )
            )
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