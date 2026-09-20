import re
import unicodedata
import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.member import Member, MemberStatus
from backend.app.schemas.member import (
    MemberAdminUpdateRequest,
    MemberUpdateRequest,
)
from backend.app.services.activity_logger import log_user_activity


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


def _member_display_name(member: Member) -> str:
    """Return a human-readable member name."""

    return (
        f"{member.first_name.strip()} "
        f"{member.last_name.strip()}"
    ).strip()


def _build_audit_changes(
    resource: Member,
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


def slugify_member_name(
    first_name: str,
    last_name: str,
) -> str:
    """
    Generate a URL-safe member slug.
    """

    value = f"{first_name}-{last_name}"

    value = unicodedata.normalize(
        "NFKD",
        value,
    ).encode(
        "ascii",
        "ignore",
    ).decode(
        "ascii",
    )

    value = value.lower()

    value = re.sub(
        r"[^a-z0-9]+",
        "-",
        value,
    )

    value = value.strip("-")

    return value


def generate_unique_slug(
    db: Session,
    first_name: str,
    last_name: str,
    *,
    exclude_member_id: uuid.UUID | None = None,
) -> str:
    """
    Generate a unique slug based on the member's name.
    """

    base_slug = slugify_member_name(
        first_name,
        last_name,
    )

    if not base_slug:
        base_slug = "member"

    slug = base_slug
    counter = 2

    while True:
        statement = select(Member.id).where(
            Member.slug == slug
        )

        if exclude_member_id is not None:
            statement = statement.where(
                Member.id != exclude_member_id
            )

        existing_id = db.scalar(statement)

        if existing_id is None:
            return slug

        slug = f"{base_slug}-{counter}"
        counter += 1


def get_member_for_user(
    db: Session,
    user_id: uuid.UUID,
) -> Member | None:
    statement = select(Member).where(
        Member.user_id == user_id
    )

    return db.scalar(statement)


def get_member(
    db: Session,
    member_id: uuid.UUID,
) -> Member:
    member = db.get(
        Member,
        member_id,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )

    return member


def get_member_by_slug(
    db: Session,
    slug: str,
) -> Member:
    statement = select(Member).where(
        Member.slug == slug
    )

    member = db.scalar(statement)

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )

    return member


def list_members(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    member_status: MemberStatus | None = None,
) -> tuple[list[Member], int]:
    """
    List public members with search, filtering and pagination.
    """

    conditions = [
        Member.status != MemberStatus.ARCHIVED,
    ]

    if member_status is not None:
        conditions.append(
            Member.status == member_status,
        )

    if search:
        search_pattern = f"%{search.strip()}%"

        conditions.append(
            or_(
                Member.first_name.ilike(search_pattern),
                Member.last_name.ilike(search_pattern),
                Member.position.ilike(search_pattern),
                Member.bio.ilike(search_pattern),
            )
        )

    count_statement = select(
        func.count(Member.id)
    ).where(
        *conditions
    )

    total = db.scalar(
        count_statement
    ) or 0

    statement = (
        select(Member)
        .where(*conditions)
        .order_by(
            Member.first_name.asc(),
            Member.last_name.asc(),
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(
        db.scalars(statement).all()
    )

    return items, total


def update_member_profile(
    db: Session,
    member: Member,
    data: MemberUpdateRequest,
) -> Member:
    """
    Update a member's own profile.
    """

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        return member

    member_name_before = _member_display_name(member)

    changes = _build_audit_changes(
        member,
        update_data,
    )

    name_changed = (
        "first_name" in update_data
        or "last_name" in update_data
    )

    for field, value in update_data.items():
        setattr(
            member,
            field,
            value,
        )

    if name_changed:
        member.slug = generate_unique_slug(
            db,
            member.first_name,
            member.last_name,
            exclude_member_id=member.id,
        )

    member_name_after = _member_display_name(member)

    log_user_activity(
        db,
        action="MEMBER_UPDATED",
        user_id=member.user_id,
        resource_type="member",
        resource_id=member.id,
        details=(
            f'Updated member "{member_name_after}"'
        ),
        activity_metadata={
            "resource_name": member_name_after,
            "actor_type": "member",
            "changed_fields": sorted(changes.keys()),
            "changes": changes,
        },
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update member profile.",
        ) from exc

    db.refresh(member)

    return member


def update_member_admin(
    db: Session,
    member: Member,
    data: MemberAdminUpdateRequest,
    *,
    actor_user_id: uuid.UUID,
) -> Member:
    """
    Update a member by staff/admin users.
    """

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        return member

    previous_status = member.status
    member_name_before = _member_display_name(member)

    changes = _build_audit_changes(
        member,
        update_data,
    )

    name_changed = (
        "first_name" in update_data
        or "last_name" in update_data
    )

    for field, value in update_data.items():
        setattr(
            member,
            field,
            value,
        )

    if name_changed:
        member.slug = generate_unique_slug(
            db,
            member.first_name,
            member.last_name,
            exclude_member_id=member.id,
        )

    new_status = member.status
    member_name_after = _member_display_name(member)

    if (
        "status" in update_data
        and new_status != previous_status
    ):
        action = {
            MemberStatus.ACTIVE: "MEMBER_REACTIVATED",
            MemberStatus.INACTIVE: "MEMBER_DEACTIVATED",
            MemberStatus.ARCHIVED: "MEMBER_ARCHIVED",
        }[new_status]
    else:
        action = "MEMBER_UPDATED"

    action_details = {
        "MEMBER_UPDATED": (
            f'Updated member "{member_name_after}"'
        ),
        "MEMBER_REACTIVATED": (
            f'Reactivated member "{member_name_after}"'
        ),
        "MEMBER_DEACTIVATED": (
            f'Deactivated member "{member_name_after}"'
        ),
        "MEMBER_ARCHIVED": (
            f'Archived member "{member_name_after}"'
        ),
    }

    log_user_activity(
        db,
        action=action,
        user_id=actor_user_id,
        resource_type="member",
        resource_id=member.id,
        details=action_details[action],
        activity_metadata={
            "resource_name": member_name_after,
            "actor_type": "staff_or_admin",
            "changed_fields": sorted(changes.keys()),
            "changes": changes,
            "previous_status": previous_status.value,
            "new_status": new_status.value,
        },
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to update member.",
        ) from exc

    db.refresh(member)

    return member


def delete_member(
    db: Session,
    member: Member,
    *,
    actor_user_id: uuid.UUID,
) -> None:
    """
    Delete a member profile.

    The linked user account is intentionally not deleted.
    """

    member_id = member.id
    member_user_id = member.user_id
    member_name = _member_display_name(member)

    db.delete(member)

    log_user_activity(
        db,
        action="MEMBER_DELETED",
        user_id=actor_user_id,
        resource_type="member",
        resource_id=member_id,
        details=(
            f'Deleted member "{member_name}"'
        ),
        activity_metadata={
            "resource_name": member_name,
            "actor_type": "admin",
            "affected_user_id": str(member_user_id),
        },
    )

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to delete member.",
        ) from exc