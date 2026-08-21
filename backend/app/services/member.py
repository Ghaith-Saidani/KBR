import re
import unicodedata
import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.member import Member, MemberStatus
from backend.app.schemas.member import (
    MemberAdminUpdateRequest,
    MemberUpdateRequest,
)


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
) -> Member:
    """
    Update a member by staff/admin users.
    """

    update_data = data.model_dump(
        exclude_unset=True,
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
) -> None:
    """
    Delete a member profile.

    The linked user account is intentionally not deleted.
    """

    db.delete(member)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Unable to delete member.",
        ) from exc
