import uuid
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.event import Event, EventStatus
from backend.app.models.notification import NotificationType
from backend.app.schemas.event import (
    EventCreateRequest,
    EventUpdateRequest,
)
from backend.app.services.activity_logger import log_user_activity
from backend.app.services.notification import (
    add_notification_for_active_members,
)


def _serialize_audit_value(value: Any) -> object:
    """Convert values to JSON-safe audit metadata."""

    if isinstance(value, Enum):
        return value.value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, uuid.UUID):
        return str(value)

    if isinstance(value, (str, int, float, bool)) or value is None:
        return value

    return str(value)


def _build_audit_changes(
    resource: Event,
    update_data: dict[str, Any],
) -> dict[str, dict[str, object]]:
    """
    Build a before/after representation for fields that
    actually changed.
    """

    changes: dict[str, dict[str, object]] = {}

    for field, new_value in update_data.items():
        previous_value = getattr(resource, field)

        serialized_previous = _serialize_audit_value(
            previous_value,
        )
        serialized_new = _serialize_audit_value(
            new_value,
        )

        if serialized_previous != serialized_new:
            changes[field] = {
                "from": serialized_previous,
                "to": serialized_new,
            }

    return changes


def get_event(
    db: Session,
    event_id: uuid.UUID,
) -> Event:
    event = db.get(Event, event_id)

    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    return event


def list_events(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    include_unpublished: bool = False,
    search: str | None = None,
    upcoming: bool | None = None,
) -> tuple[list[Event], int]:
    """
    Return events with optional filtering and pagination.

    Public users only receive published events.
    Staff/admin callers can optionally include unpublished events.
    """

    filters = []

    if not include_unpublished:
        filters.append(
            Event.status == EventStatus.PUBLISHED
        )

    if search:
        search_pattern = f"%{search.strip()}%"

        filters.append(
            or_(
                Event.title.ilike(search_pattern),
                Event.description.ilike(search_pattern),
                Event.location.ilike(search_pattern),
            )
        )

    if upcoming is True:
        filters.append(
            Event.start_at >= datetime.now(timezone.utc)
        )

    elif upcoming is False:
        filters.append(
            Event.start_at < datetime.now(timezone.utc)
        )

    count_statement = select(
        func.count(Event.id)
    )

    statement = select(Event)

    if filters:
        count_statement = count_statement.where(*filters)
        statement = statement.where(*filters)

    total = db.scalar(count_statement) or 0

    statement = (
        statement
        .order_by(
            Event.start_at.asc(),
            Event.id.asc(),
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(
        db.scalars(statement).all()
    )

    return items, total


def create_event(
    db: Session,
    data: EventCreateRequest,
    current_user_id: uuid.UUID,
) -> Event:
    """
    Create a new event.

    If the event is created directly as published,
    notify all active members.
    """

    event = Event(
        title=data.title,
        description=data.description,
        location=data.location,
        start_at=data.start_at,
        end_at=data.end_at,
        cover_image=data.cover_image,
        status=data.status,
        created_by=current_user_id,
    )

    db.add(event)
    db.flush()

    event_title = event.title.strip()

    log_user_activity(
        db,
        action="EVENT_CREATED",
        user_id=current_user_id,
        resource_type="event",
        resource_id=event.id,
        details=f'Created event "{event_title}"',
        activity_metadata={
            "resource_name": event_title,
            "status": event.status.value,
        },
    )

    if data.status == EventStatus.PUBLISHED:
        add_notification_for_active_members(
            db,
            title="Nouvel événement",
            message=(
                "Un nouvel événement KBR est disponible : "
                f"{event_title}."
            ),
            notification_type=NotificationType.INFO,
        )

    db.commit()
    db.refresh(event)

    return event


def update_event(
    db: Session,
    event_id: uuid.UUID,
    data: EventUpdateRequest,
    *,
    actor_user_id: uuid.UUID,
) -> Event:
    """
    Update an existing event.

    A notification is generated only when an event transitions
    from a non-published state to published.
    """

    event = get_event(
        db,
        event_id,
    )

    previous_status = event.status

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        return event

    final_start_at = update_data.get(
        "start_at",
        event.start_at,
    )

    final_end_at = update_data.get(
        "end_at",
        event.end_at,
    )

    if (
        final_end_at is not None
        and final_end_at <= final_start_at
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_at must be later than start_at.",
        )

    changes = _build_audit_changes(
        event,
        update_data,
    )

    changed_fields = sorted(changes.keys())

    for field, value in update_data.items():
        setattr(
            event,
            field,
            value,
        )

    became_published = (
        previous_status != EventStatus.PUBLISHED
        and event.status == EventStatus.PUBLISHED
    )

    if became_published:
        add_notification_for_active_members(
            db,
            title="Nouvel événement",
            message=(
                "Un nouvel événement KBR est disponible : "
                f"{event.title.strip()}."
            ),
            notification_type=NotificationType.INFO,
        )

    event_title = event.title.strip()

    if became_published:
        action = "EVENT_PUBLISHED"
        details = (
            f'Published event "{event_title}"'
        )
    elif (
        "status" in update_data
        and event.status == EventStatus.CANCELLED
        and previous_status != EventStatus.CANCELLED
    ):
        action = "EVENT_CANCELLED"
        details = (
            f'Cancelled event "{event_title}"'
        )
    else:
        action = "EVENT_UPDATED"
        details = (
            f'Updated event "{event_title}"'
        )

    log_user_activity(
        db,
        action=action,
        user_id=actor_user_id,
        resource_type="event",
        resource_id=event.id,
        details=details,
        activity_metadata={
            "resource_name": event_title,
            "changed_fields": changed_fields,
            "changes": changes,
            "previous_status": previous_status.value,
            "new_status": event.status.value,
        },
    )

    db.commit()
    db.refresh(event)

    return event


def delete_event(
    db: Session,
    event_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID,
) -> None:
    """
    Permanently delete an event.
    """

    event = get_event(
        db,
        event_id,
    )

    event_id = event.id
    event_title = event.title.strip()

    db.delete(event)

    log_user_activity(
        db,
        action="EVENT_DELETED",
        user_id=actor_user_id,
        resource_type="event",
        resource_id=event_id,
        details=(
            f'Deleted event "{event_title}"'
        ),
        activity_metadata={
            "resource_name": event_title,
        },
    )

    db.commit()