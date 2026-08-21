import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.permissions import require_admin
from backend.app.models.user import User
from backend.app.schemas.admin import (
    AdminMemberListResponse,
    AdminMemberResponse,
    AdminMemberUpdateRequest,
    AdminRoleUpdateRequest,
)
from backend.app.services.admin import (
    activate_member,
    get_admin_member,
    list_members,
    suspend_member,
    update_member,
    update_member_role,
)


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


def build_member_response(
    user: User,
    member,
) -> AdminMemberResponse:
    """
    Build the administrative member response.
    """

    return AdminMemberResponse(
        user_id=user.id,
        member_id=member.id,
        email=user.email,
        first_name=member.first_name,
        last_name=member.last_name,
        phone=member.phone,
        profile_image=member.profile_image,
        bio=member.bio,
        joined_at=member.joined_at,
        role=user.role,
        status=user.status,
        is_email_verified=user.is_email_verified,
        created_at=member.created_at,
        updated_at=member.updated_at,
    )


@router.get(
    "/members",
    response_model=AdminMemberListResponse,
)
def get_members(
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminMemberListResponse:
    """
    List all KBR members.
    """

    items, total = list_members(
        db,
        skip=skip,
        limit=limit,
    )

    return AdminMemberListResponse(
        items=[
            build_member_response(
                user,
                member,
            )
            for user, member in items
        ],
        total=total,
    )


@router.get(
    "/members/{member_id}",
    response_model=AdminMemberResponse,
)
def get_member(
    member_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminMemberResponse:
    """
    Get a member with administrative information.
    """

    user, member = get_admin_member(
        db,
        member_id,
    )

    return build_member_response(
        user,
        member,
    )


@router.patch(
    "/members/{member_id}",
    response_model=AdminMemberResponse,
)
def update_member_profile(
    member_id: uuid.UUID,
    data: AdminMemberUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminMemberResponse:
    """
    Update a member profile as an administrator.
    """

    user, member = update_member(
        db,
        member_id,
        data,
    )

    return build_member_response(
        user,
        member,
    )


@router.post(
    "/members/{member_id}/activate",
    response_model=AdminMemberResponse,
)
def activate_member_account(
    member_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminMemberResponse:
    """
    Activate a member account.
    """

    user, member = activate_member(
        db,
        member_id,
    )

    return build_member_response(
        user,
        member,
    )


@router.post(
    "/members/{member_id}/suspend",
    response_model=AdminMemberResponse,
)
def suspend_member_account(
    member_id: uuid.UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminMemberResponse:
    """
    Suspend a member account.
    """

    user, member = suspend_member(
        db,
        member_id,
        current_admin=current_user,
    )

    return build_member_response(
        user,
        member,
    )


@router.patch(
    "/members/{member_id}/role",
    response_model=AdminMemberResponse,
)
def change_member_role(
    member_id: uuid.UUID,
    data: AdminRoleUpdateRequest,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminMemberResponse:
    """
    Change a member's role.
    """

    user, member = update_member_role(
        db,
        member_id,
        data.role,
        current_admin=current_user,
    )

    return build_member_response(
        user,
        member,
    )