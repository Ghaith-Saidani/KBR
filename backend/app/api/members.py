from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.models.member import Member
from backend.app.models.user import User
from backend.app.schemas.member import (
    MemberResponse,
    MemberUpdateRequest,
    PublicMemberResponse,
)


router = APIRouter(
    prefix="/members",
    tags=["members"],
)


def get_member_for_user(
    db: Session,
    user_id: UUID,
) -> Member | None:
    """Find a member profile belonging to a user."""

    statement = select(Member).where(
        Member.user_id == user_id
    )

    return db.scalar(statement)


@router.get(
    "/me",
    response_model=MemberResponse,
)
def get_my_member_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Member:
    """Return the authenticated user's member profile."""

    member = get_member_for_user(
        db,
        current_user.id,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found.",
        )

    return member


@router.patch(
    "/me",
    response_model=MemberResponse,
)
def update_my_member_profile(
    data: MemberUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Member:
    """Update the authenticated user's member profile."""

    member = get_member_for_user(
        db,
        current_user.id,
    )

    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found.",
        )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(
            member,
            field,
            value,
        )

    db.commit()
    db.refresh(member)

    return member


@router.get(
    "/{member_id}",
    response_model=PublicMemberResponse,
)
def get_member_profile(
    member_id: UUID,
    db: Session = Depends(get_db),
) -> Member:
    """
    Return a public member profile by ID.

    Private fields such as phone and user_id
    are not exposed.
    """

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