import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.app.models.member import Member
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.admin import (
    AdminDashboardResponse,
    AdminMemberStats,
    AdminMemberUpdateRequest,
    AdminUserStats,
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
    resource: Any,
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


def get_admin_member(
    db: Session,
    member_id: uuid.UUID,
) -> tuple[User, Member]:
    statement = (
        select(User, Member)
        .join(
            Member,
            Member.user_id == User.id,
        )
        .where(
            Member.id == member_id,
        )
    )

    result = db.execute(statement).first()

    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )

    user, member = result

    return user, member


def list_members(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    search: str | None = None,
    role: UserRole | None = None,
    status_filter: UserStatus | None = None,
) -> tuple[list[tuple[User, Member]], int]:
    """
    List members with optional search, role and status filters.
    """

    conditions = []

    if search:
        search_value = f"%{search.strip()}%"

        conditions.append(
            or_(
                User.email.ilike(search_value),
                Member.first_name.ilike(search_value),
                Member.last_name.ilike(search_value),
            )
        )

    if role is not None:
        conditions.append(
            User.role == role,
        )

    if status_filter is not None:
        conditions.append(
            User.status == status_filter,
        )

    count_statement = (
        select(
            func.count(Member.id),
        )
        .join(
            User,
            Member.user_id == User.id,
        )
    )

    if conditions:
        count_statement = count_statement.where(
            *conditions,
        )

    total = db.scalar(
        count_statement,
    ) or 0

    statement = (
        select(User, Member)
        .join(
            Member,
            Member.user_id == User.id,
        )
    )

    if conditions:
        statement = statement.where(
            *conditions,
        )

    statement = (
        statement
        .order_by(
            Member.created_at.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(
        db.execute(statement).all()
    )

    return items, total


def get_dashboard_stats(
    db: Session,
) -> AdminDashboardResponse:
    total_members = (
        db.scalar(
            select(func.count(Member.id))
        )
        or 0
    )

    pending_members = (
        db.scalar(
            select(func.count(Member.id))
            .join(
                User,
                Member.user_id == User.id,
            )
            .where(
                User.status == UserStatus.PENDING
            )
        )
        or 0
    )

    active_members = (
        db.scalar(
            select(func.count(Member.id))
            .join(
                User,
                Member.user_id == User.id,
            )
            .where(
                User.status == UserStatus.ACTIVE
            )
        )
        or 0
    )

    suspended_members = (
        db.scalar(
            select(func.count(Member.id))
            .join(
                User,
                Member.user_id == User.id,
            )
            .where(
                User.status == UserStatus.SUSPENDED
            )
        )
        or 0
    )

    total_users = (
        db.scalar(
            select(func.count(User.id))
        )
        or 0
    )

    member_users = (
        db.scalar(
            select(func.count(User.id))
            .where(
                User.role == UserRole.MEMBER
            )
        )
        or 0
    )

    staff_users = (
        db.scalar(
            select(func.count(User.id))
            .where(
                User.role == UserRole.STAFF
            )
        )
        or 0
    )

    admin_users = (
        db.scalar(
            select(func.count(User.id))
            .where(
                User.role == UserRole.ADMIN
            )
        )
        or 0
    )

    return AdminDashboardResponse(
        members=AdminMemberStats(
            total=total_members,
            pending=pending_members,
            active=active_members,
            suspended=suspended_members,
        ),
        users=AdminUserStats(
            total=total_users,
            members=member_users,
            staff=staff_users,
            admins=admin_users,
        ),
    )


def update_member(
    db: Session,
    member_id: uuid.UUID,
    data: AdminMemberUpdateRequest,
    *,
    actor_user_id: uuid.UUID,
) -> tuple[User, Member]:
    """
    Update a member profile as an administrator and record
    a semantic MEMBER_UPDATED audit event.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        return user, member

    changes = _build_audit_changes(
        member,
        update_data,
    )

    if not changes:
        return user, member

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()

        setattr(
            member,
            field,
            value,
        )

    member_name = _member_display_name(member)

    log_user_activity(
        db,
        action="MEMBER_UPDATED",
        user_id=actor_user_id,
        resource_type="member",
        resource_id=member.id,
        details=(
            f'Updated member "{member_name}"'
        ),
        activity_metadata={
            "resource_name": member_name,
            "actor_type": "staff_or_admin",
            "changed_fields": sorted(changes.keys()),
            "changes": changes,
        },
    )

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member


def activate_member(
    db: Session,
    member_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID,
) -> tuple[User, Member]:
    """
    Activate a member account and record a semantic
    MEMBER_REACTIVATED audit event.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    if user.status == UserStatus.ACTIVE:
        return user, member

    previous_status = user.status

    user.status = UserStatus.ACTIVE

    member_name = _member_display_name(member)

    log_user_activity(
        db,
        action="MEMBER_REACTIVATED",
        user_id=actor_user_id,
        resource_type="member",
        resource_id=member.id,
        details=(
            f'Reactivated member "{member_name}"'
        ),
        activity_metadata={
            "resource_name": member_name,
            "actor_type": "staff_or_admin",
            "changed_fields": ["status"],
            "changes": {
                "status": {
                    "from": _serialize_audit_value(
                        previous_status,
                    ),
                    "to": _serialize_audit_value(
                        user.status,
                    ),
                },
            },
            "previous_status": _serialize_audit_value(
                previous_status,
            ),
            "new_status": _serialize_audit_value(
                user.status,
            ),
        },
    )

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member


def suspend_member(
    db: Session,
    member_id: uuid.UUID,
    *,
    actor_user_id: uuid.UUID,
) -> tuple[User, Member]:
    """
    Suspend a member account and record a semantic
    MEMBER_DEACTIVATED audit event.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    previous_status = user.status

    if previous_status == UserStatus.SUSPENDED:
        return user, member

    user.status = UserStatus.SUSPENDED

    member_name = _member_display_name(member)

    log_user_activity(
        db,
        action="MEMBER_DEACTIVATED",
        user_id=actor_user_id,
        resource_type="member",
        resource_id=member.id,
        details=(
            f'Deactivated member "{member_name}"'
        ),
        activity_metadata={
            "resource_name": member_name,
            "actor_type": "staff_or_admin",
            "changed_fields": ["status"],
            "changes": {
                "status": {
                    "from": _serialize_audit_value(
                        previous_status,
                    ),
                    "to": _serialize_audit_value(
                        user.status,
                    ),
                },
            },
            "previous_status": _serialize_audit_value(
                previous_status,
            ),
            "new_status": _serialize_audit_value(
                user.status,
            ),
        },
    )

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member


def update_member_role(
    db: Session,
    member_id: uuid.UUID,
    role: UserRole,
    *,
    actor_user_id: uuid.UUID,
) -> tuple[User, Member]:
    """
    Change a member's role and record the operation as a
    MEMBER_UPDATED audit event.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    previous_role = user.role

    if previous_role == role:
        return user, member

    user.role = role

    member_name = _member_display_name(member)

    log_user_activity(
        db,
        action="MEMBER_UPDATED",
        user_id=actor_user_id,
        resource_type="member",
        resource_id=member.id,
        details=(
            f'Updated member "{member_name}"'
        ),
        activity_metadata={
            "resource_name": member_name,
            "actor_type": "staff_or_admin",
            "changed_fields": ["role"],
            "changes": {
                "role": {
                    "from": _serialize_audit_value(
                        previous_role,
                    ),
                    "to": _serialize_audit_value(
                        role,
                    ),
                },
            },
        },
    )

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member