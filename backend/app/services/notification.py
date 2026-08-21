import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from backend.app.models.notification import (
    Notification,
    NotificationType,
)


def create_notification(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str,
    message: str,
    notification_type: NotificationType = NotificationType.INFO,
) -> Notification:
    """
    Create a notification for a specific user.

    This function is intended to be used internally by other services
    such as events, news, activities, administration, and authentication.
    """

    notification = Notification(
        user_id=user_id,
        type=notification_type,
        title=title.strip(),
        message=message.strip(),
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification


def get_notification(
    db: Session,
    *,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Notification:
    """
    Get a notification belonging to the authenticated user.
    """

    statement = select(Notification).where(
        Notification.id == notification_id,
        Notification.user_id == user_id,
    )

    notification = db.scalar(statement)

    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )

    return notification


def list_notifications(
    db: Session,
    *,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 50,
    unread_only: bool = False,
) -> tuple[list[Notification], int, int]:
    """
    List notifications belonging to a user.

    Returns:
        notifications,
        total matching notifications,
        total unread notifications
    """

    conditions = [
        Notification.user_id == user_id,
    ]

    if unread_only:
        conditions.append(
            Notification.is_read.is_(False),
        )

    total_statement = select(
        func.count(Notification.id)
    ).where(
        *conditions,
    )

    total = db.scalar(total_statement) or 0

    unread_statement = select(
        func.count(Notification.id)
    ).where(
        Notification.user_id == user_id,
        Notification.is_read.is_(False),
    )

    unread_count = db.scalar(unread_statement) or 0

    statement = (
        select(Notification)
        .where(*conditions)
        .order_by(
            Notification.created_at.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(
        db.scalars(statement).all()
    )

    return items, total, unread_count


def get_unread_count(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> int:
    """
    Return the number of unread notifications for a user.
    """

    statement = select(
        func.count(Notification.id)
    ).where(
        Notification.user_id == user_id,
        Notification.is_read.is_(False),
    )

    return db.scalar(statement) or 0


def mark_notification_as_read(
    db: Session,
    *,
    notification: Notification,
) -> Notification:
    """
    Mark a single notification as read.
    """

    if notification.is_read:
        return notification

    notification.is_read = True
    notification.read_at = datetime.now(
        timezone.utc
    )

    db.commit()
    db.refresh(notification)

    return notification


def mark_all_notifications_as_read(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> int:
    """
    Mark all unread notifications belonging to a user as read.

    Returns the number of notifications updated.
    """

    now = datetime.now(timezone.utc)

    statement = (
        update(Notification)
        .where(
            Notification.user_id == user_id,
            Notification.is_read.is_(False),
        )
        .values(
            is_read=True,
            read_at=now,
        )
    )

    result = db.execute(statement)

    db.commit()

    return result.rowcount or 0
