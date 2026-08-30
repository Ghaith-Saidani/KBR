import uuid
from collections.abc import Mapping
from datetime import datetime

from sqlalchemy.orm import Session

from backend.app.models.user_activity import UserActivity


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
    Create and persist a user activity log.

    This function is intentionally centralized so that all parts
    of the application use the same activity-log creation logic.
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