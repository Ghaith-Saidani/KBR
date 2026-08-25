import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.core.permissions import require_staff
from backend.app.models.event import Event, EventStatus
from backend.app.models.user import User
from backend.app.schemas.event import (
    EventCreateRequest,
    EventListResponse,
    EventResponse,
    EventUpdateRequest,
)
from backend.app.services.event import (
    create_event,
    delete_event,
    get_event,
    list_events,
    update_event,
)


router = APIRouter(
    prefix="/events",
    tags=["events"],
)


@router.get(
    "",
    response_model=EventListResponse,
    summary="List published events",
    description=(
        "Return published events visible to the public. "
        "Results can be searched and filtered by whether they are upcoming."
    ),
)
def get_events(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of events to skip.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of events to return.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search title, description, or location.",
    ),
    upcoming: bool | None = Query(
        default=None,
        description=(
            "Filter events by date. "
            "true = upcoming, false = past."
        ),
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> EventListResponse:
    items, total = list_events(
        db,
        skip=skip,
        limit=limit,
        include_unpublished=False,
        search=search,
        upcoming=upcoming,
    )

    return EventListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get a published event",
    description="Return a single published event.",
    responses={
        404: {
            "description": "Event not found.",
        },
    },
)
def get_event_details(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Event:
    event = get_event(
        db,
        event_id,
    )

    if event.status != EventStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found.",
        )

    return event


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an event",
    description=(
        "Create an event. "
        "Staff members and administrators can create events."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        403: {
            "description": "Staff privileges required.",
        },
        422: {
            "description": "Invalid event data.",
        },
    },
)
def create_new_event(
    data: EventCreateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> EventResponse:
    return create_event(
        db,
        data,
        current_user.id,
    )


@router.patch(
    "/{event_id}",
    response_model=EventResponse,
    summary="Update an event",
    description=(
        "Update an existing event. "
        "Only provided fields are modified."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        403: {
            "description": "Staff privileges required.",
        },
        404: {
            "description": "Event not found.",
        },
        422: {
            "description": "Invalid event data.",
        },
    },
)
def update_existing_event(
    event_id: uuid.UUID,
    data: EventUpdateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> EventResponse:
    return update_event(
        db,
        event_id,
        data,
    )


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an event",
    description=(
        "Permanently delete an event. "
        "Only staff members and administrators can delete events."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        403: {
            "description": "Staff privileges required.",
        },
        404: {
            "description": "Event not found.",
        },
    },
)
def delete_existing_event(
    event_id: uuid.UUID,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> None:
    delete_event(
        db,
        event_id,
    )