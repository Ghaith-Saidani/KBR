import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user, security
from backend.app.core.database import get_db
from backend.app.core.permissions import require_admin, require_staff
from backend.app.models.contact import ContactMessage, ContactMessageStatus
from backend.app.models.user import User
from backend.app.schemas.contact import (
    ContactMessageCreateRequest,
    ContactMessageListResponse,
    ContactMessageResponse,
    ContactMessageUpdateRequest,
)
from backend.app.services.contact import (
    create_contact_message,
    delete_contact_message,
    get_contact_message,
    list_contact_messages,
    update_contact_message,
)


router = APIRouter(
    prefix="/contact",
    tags=["contact"],
)


def get_optional_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Resolve the authenticated user when a valid bearer token is provided.

    Contact form submissions remain public. If a user is authenticated,
    their contact message is associated with their account.
    """

    if credentials is None:
        return None

    return get_current_user(
        request=request,
        credentials=credentials,
        db=db,
    )


@router.post(
    "",
    response_model=ContactMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a contact message",
    description=(
        "Submit a contact message. Authentication is optional. "
        "Authenticated users have their message associated with their account."
    ),
)
def submit_contact_message(
    data: ContactMessageCreateRequest,
    current_user: User | None = Depends(get_optional_current_user),
    db: Session = Depends(get_db),
) -> ContactMessage:
    return create_contact_message(
        db,
        data,
        user_id=current_user.id if current_user is not None else None,
    )


@router.get(
    "",
    response_model=ContactMessageListResponse,
    summary="List contact messages",
    description="List contact messages for staff and administrators.",
)
def get_contact_messages(
    status_filter: ContactMessageStatus | None = Query(
        default=None,
        alias="status",
        description="Filter by message status.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search name, email, subject, or message.",
    ),
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of messages to skip.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of messages to return.",
    ),
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> ContactMessageListResponse:
    items, total = list_contact_messages(
        db,
        skip=skip,
        limit=limit,
        message_status=status_filter,
        search=search,
    )

    return ContactMessageListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{message_id}",
    response_model=ContactMessageResponse,
    summary="Get a contact message",
    description="Get a single contact message for staff and administrators.",
    responses={
        404: {
            "description": "Contact message not found.",
        },
    },
)
def get_contact_message_details(
    message_id: uuid.UUID,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> ContactMessage:
    return get_contact_message(
        db,
        message_id,
    )


@router.patch(
    "/{message_id}",
    response_model=ContactMessageResponse,
    summary="Update a contact message",
    description="Update the status of a contact message.",
    responses={
        404: {
            "description": "Contact message not found.",
        },
    },
)
def update_contact_message_endpoint(
    message_id: uuid.UUID,
    data: ContactMessageUpdateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> ContactMessage:
    return update_contact_message(
        db,
        message_id,
        data,
    )


@router.delete(
    "/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contact message",
    description="Permanently delete a contact message. Administrators only.",
    responses={
        404: {
            "description": "Contact message not found.",
        },
    },
)
def delete_contact_message_endpoint(
    message_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    delete_contact_message(
        db,
        message_id,
    )

    return None