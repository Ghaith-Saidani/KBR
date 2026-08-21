import uuid

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
) -> tuple[User, Member]:
    user, member = get_admin_member(
        db,
        member_id,
    )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip()

        setattr(
            member,
            field,
            value,
        )

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member


def activate_member(
    db: Session,
    member_id: uuid.UUID,
) -> tuple[User, Member]:
    user, member = get_admin_member(
        db,
        member_id,
    )

    if user.status == UserStatus.ACTIVE:
        return user, member

    user.status = UserStatus.ACTIVE

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member


def suspend_member(
    db: Session,
    member_id: uuid.UUID,
) -> tuple[User, Member]:
    user, member = get_admin_member(
        db,
        member_id,
    )

    user.status = UserStatus.SUSPENDED

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member


def update_member_role(
    db: Session,
    member_id: uuid.UUID,
    role: UserRole,
) -> tuple[User, Member]:
    user, member = get_admin_member(
        db,
        member_id,
    )

    user.role = role

    db.commit()

    db.refresh(user)
    db.refresh(member)

    return user, member