import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.contact import ContactMessage, ContactMessageStatus
from backend.app.schemas.contact import (
    ContactMessageCreateRequest,
    ContactMessageUpdateRequest,
)


def create_contact_message(
    db: Session,
    data: ContactMessageCreateRequest,
    user_id: uuid.UUID | None = None,
) -> ContactMessage:
    """
    Create a new contact message.

    The message can optionally be associated with an authenticated user.
    """

    contact_message = ContactMessage(
        id=uuid.uuid4(),
        name=data.name,
        email=str(data.email),
        subject=data.subject,
        message=data.message,
        status=ContactMessageStatus.NEW,
        user_id=user_id,
    )

    db.add(contact_message)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to create contact message.",
        ) from exc

    db.refresh(contact_message)

    return contact_message


def get_contact_message(
    db: Session,
    message_id: uuid.UUID,
) -> ContactMessage:
    """
    Get a contact message by ID.
    """

    contact_message = db.get(
        ContactMessage,
        message_id,
    )

    if contact_message is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact message not found.",
        )

    return contact_message


def list_contact_messages(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    message_status: ContactMessageStatus | None = None,
) -> tuple[list[ContactMessage], int]:
    """
    List contact messages with pagination, search, and status filtering.
    """

    conditions = []

    if message_status is not None:
        conditions.append(
            ContactMessage.status == message_status,
        )

    if search:
        search_pattern = f"%{search.strip()}%"

        conditions.append(
            or_(
                ContactMessage.name.ilike(search_pattern),
                ContactMessage.email.ilike(search_pattern),
                ContactMessage.subject.ilike(search_pattern),
                ContactMessage.message.ilike(search_pattern),
            )
        )

    count_statement = select(
        func.count(ContactMessage.id),
    )

    if conditions:
        count_statement = count_statement.where(
            *conditions,
        )

    total = db.scalar(
        count_statement,
    ) or 0

    statement = (
        select(ContactMessage)
        .where(*conditions)
        .order_by(ContactMessage.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    items = list(
        db.scalars(statement).all()
    )

    return items, total


def update_contact_message(
    db: Session,
    message_id: uuid.UUID,
    data: ContactMessageUpdateRequest,
) -> ContactMessage:
    """
    Update the status of a contact message.
    """

    contact_message = get_contact_message(
        db,
        message_id,
    )

    contact_message.status = data.status

    db.commit()
    db.refresh(contact_message)

    return contact_message


def delete_contact_message(
    db: Session,
    message_id: uuid.UUID,
) -> None:
    """
    Permanently delete a contact message.
    """

    contact_message = get_contact_message(
        db,
        message_id,
    )

    db.delete(contact_message)
    db.commit()