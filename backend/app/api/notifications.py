from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.notification import Notification
from backend.app.models.user import User
from backend.app.schemas.notification import (
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationReadResponse,
    NotificationResponse,
    NotificationUnreadCountResponse,
)
from backend.app.services.notification import (
    get_notification,
    get_unread_count,
    list_notifications,
    mark_all_notifications_as_read,
    mark_notification_as_read,
)


router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
)


@router.get(
    "",
    response_model=NotificationListResponse,
    summary="List my notifications",
)
def get_notifications(
    unread_only: bool = Query(
        default=False,
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationListResponse:
    """
    Return notifications belonging to the authenticated user.
    """

    items, total, unread_count = list_notifications(
        db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        unread_only=unread_only,
    )

    return NotificationListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        unread_count=unread_count,
    )


@router.get(
    "/unread-count",
    response_model=NotificationUnreadCountResponse,
    summary="Get my unread notification count",
)
def get_my_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationUnreadCountResponse:
    """
    Return the number of unread notifications for the authenticated user.
    """

    unread_count = get_unread_count(
        db,
        user_id=current_user.id,
    )

    return NotificationUnreadCountResponse(
        unread_count=unread_count,
    )


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationReadResponse,
    summary="Mark a notification as read",
)
def read_notification(
    notification_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationReadResponse:
    """
    Mark one of the authenticated user's notifications as read.
    """

    notification = get_notification(
        db,
        notification_id=notification_id,
        user_id=current_user.id,
    )

    notification = mark_notification_as_read(
        db,
        notification=notification,
    )

    return NotificationReadResponse(
        message="Notification marked as read.",
        notification=notification,
    )


@router.post(
    "/read-all",
    response_model=NotificationReadAllResponse,
    summary="Mark all notifications as read",
)
def read_all_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NotificationReadAllResponse:
    """
    Mark every unread notification belonging to the authenticated user
    as read.
    """

    updated_count = mark_all_notifications_as_read(
        db,
        user_id=current_user.id,
    )

    return NotificationReadAllResponse(
        message="All notifications marked as read.",
        updated_count=updated_count,
    )
