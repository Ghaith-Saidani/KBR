import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.permissions import require_member, require_staff
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
        "Return published events visible to authenticated KBR members. "
        "Results can be searched and filtered by whether they are upcoming."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
    },
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
    current_user: User = Depends(require_member),
    db: Session = Depends(get_db),
) -> EventListResponse:
    del current_user

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
    "/manage",
    response_model=EventListResponse,
    summary="List all events for staff",
    description=(
        "Return all events, including drafts and cancelled events. "
        "Staff members and administrators only."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        403: {
            "description": "Staff privileges required.",
        },
    },
)
def get_events_for_management(
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
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> EventListResponse:
    del current_user

    items, total = list_events(
        db,
        skip=skip,
        limit=limit,
        include_unpublished=True,
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
    description=(
        "Return a single published event to an authenticated "
        "KBR member."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        404: {
            "description": "Event not found.",
        },
    },
)
def get_event_details(
    event_id: uuid.UUID,
    current_user: User = Depends(require_member),
    db: Session = Depends(get_db),
) -> Event:
    del current_user

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
    del current_user

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
    del current_user

    delete_event(
        db,
        event_id,
    )