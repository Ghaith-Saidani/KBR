import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from backend.app.models.member import Member
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.admin import AdminMemberUpdateRequest


def get_admin_member(
    db: Session,
    member_id: uuid.UUID,
) -> tuple[User, Member]:
    """
    Retrieve a user and their member profile by member ID.
    """

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
) -> tuple[list[tuple[User, Member]], int]:
    """
    Return paginated members and the total member count.
    """

    count_statement = select(
        func.count(Member.id)
    )

    total = db.scalar(
        count_statement
    ) or 0

    statement = (
        select(User, Member)
        .join(
            Member,
            Member.user_id == User.id,
        )
        .order_by(
            Member.created_at.desc()
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(
        db.execute(statement).all()
    )

    return items, total


def update_member(
    db: Session,
    member_id: uuid.UUID,
    data: AdminMemberUpdateRequest,
) -> tuple[User, Member]:
    """
    Update a member's profile as an administrator.
    """

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

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update member profile.",
        )

    db.refresh(user)
    db.refresh(member)

    return user, member


def activate_member(
    db: Session,
    member_id: uuid.UUID,
) -> tuple[User, Member]:
    """
    Activate a member account.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    if user.status == UserStatus.ACTIVE:
        return user, member

    user.status = UserStatus.ACTIVE

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to activate member account.",
        )

    db.refresh(user)
    db.refresh(member)

    return user, member


def suspend_member(
    db: Session,
    member_id: uuid.UUID,
    current_admin: User,
) -> tuple[User, Member]:
    """
    Suspend a member account.

    Administrators cannot suspend themselves
    or another administrator.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot suspend your own account.",
        )

    if user.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrator accounts cannot be suspended.",
        )

    if user.status == UserStatus.SUSPENDED:
        return user, member

    user.status = UserStatus.SUSPENDED

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to suspend member account.",
        )

    db.refresh(user)
    db.refresh(member)

    return user, member


def count_admins(
    db: Session,
) -> int:
    """
    Count the number of administrator accounts.
    """

    statement = select(
        func.count(User.id)
    ).where(
        User.role == UserRole.ADMIN
    )

    return db.scalar(statement) or 0


def update_member_role(
    db: Session,
    member_id: uuid.UUID,
    role: UserRole,
    current_admin: User,
) -> tuple[User, Member]:
    """
    Change a member's role.

    Administrators cannot change their own role.
    The last administrator cannot be removed.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role.",
        )

    if user.role == role:
        return user, member

    if (
        user.role == UserRole.ADMIN
        and role != UserRole.ADMIN
    ):
        admin_count = count_admins(db)

        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The last administrator cannot be removed.",
            )

    user.role = role

    try:
        db.commit()

    except SQLAlchemyError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to change member role.",
        )

    db.refresh(user)
    db.refresh(member)

    return user, member