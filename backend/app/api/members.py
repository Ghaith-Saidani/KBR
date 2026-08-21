from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.core.permissions import require_admin, require_staff
from backend.app.models.member import Member, MemberStatus
from backend.app.models.user import User
from backend.app.schemas.member import (
    MemberAdminUpdateRequest,
    MemberListResponse,
    MemberResponse,
    MemberUpdateRequest,
    PublicMemberResponse,
)
from backend.app.services.member import (
    delete_member,
    get_member,
    get_member_by_slug,
    get_member_for_user,
    list_members,
    update_member_admin,
    update_member_profile,
)


router = APIRouter(
    prefix="/members",
    tags=["members"],
)


@router.get(
    "",
    response_model=MemberListResponse,
    summary="List public members",
)
def get_members(
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    status_filter: MemberStatus | None = Query(
        default=None,
        alias="status",
    ),
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
) -> MemberListResponse:
    items, total = list_members(
        db,
        skip=skip,
        limit=limit,
        search=search,
        member_status=status_filter,
    )

    return MemberListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/me",
    response_model=MemberResponse,
    summary="Get my member profile",
)
def get_my_member_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Member:
    member = get_member_for_user(
        db,
        current_user.id,
    )

    if member is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found.",
        )

    return member


@router.patch(
    "/me",
    response_model=MemberResponse,
    summary="Update my member profile",
)
def update_my_member_profile(
    data: MemberUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Member:
    member = get_member_for_user(
        db,
        current_user.id,
    )

    if member is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member profile not found.",
        )

    return update_member_profile(
        db,
        member,
        data,
    )


@router.get(
    "/slug/{slug}",
    response_model=PublicMemberResponse,
    summary="Get member by slug",
)
def get_member_profile_by_slug(
    slug: str,
    db: Session = Depends(get_db),
) -> Member:
    return get_member_by_slug(
        db,
        slug,
    )


@router.get(
    "/{member_id}",
    response_model=PublicMemberResponse,
    summary="Get member by ID",
)
def get_member_profile(
    member_id: UUID,
    db: Session = Depends(get_db),
) -> Member:
    return get_member(
        db,
        member_id,
    )


@router.patch(
    "/{member_id}",
    response_model=MemberResponse,
    summary="Update member",
)
def update_member(
    member_id: UUID,
    data: MemberAdminUpdateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> Member:
    member = get_member(
        db,
        member_id,
    )

    return update_member_admin(
        db,
        member,
        data,
    )


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete member",
)
def remove_member(
    member_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> None:
    member = get_member(
        db,
        member_id,
    )

    delete_member(
        db,
        member,
    )
