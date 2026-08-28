import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.permissions import require_staff
from backend.app.models.activity import Activity, ActivityStatus
from backend.app.models.user import User
from backend.app.schemas.activity import (
    ActivityCreateRequest,
    ActivityListResponse,
    ActivityResponse,
    ActivityUpdateRequest,
)
from backend.app.services.activity import (
    create_activity,
    delete_activity,
    get_activity,
    get_activity_by_slug,
    list_activities,
    update_activity,
)


router = APIRouter(
    prefix="/activities",
    tags=["activities"],
)


# ============================================================
# PUBLIC
# ============================================================


@router.get(
    "",
    response_model=ActivityListResponse,
    summary="List published activities",
)
def get_public_activities(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    db: Session = Depends(get_db),
) -> ActivityListResponse:
    items, total = list_activities(
        db,
        skip=skip,
        limit=limit,
        include_unpublished=False,
        search=search,
    )

    return ActivityListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/manage",
    response_model=ActivityListResponse,
    summary="List all activities for staff",
)
def get_activities_for_management(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> ActivityListResponse:
    del current_user

    items, total = list_activities(
        db,
        skip=skip,
        limit=limit,
        include_unpublished=True,
        search=search,
    )

    return ActivityListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/slug/{slug}",
    response_model=ActivityResponse,
    summary="Get published activity by slug",
)
def get_public_activity_by_slug(
    slug: str,
    db: Session = Depends(get_db),
) -> Activity:
    activity = get_activity_by_slug(
        db,
        slug,
    )

    if activity.status != ActivityStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found.",
        )

    return activity


@router.get(
    "/manage/{activity_id}",
    response_model=ActivityResponse,
    summary="Get an activity for management",
)
def get_activity_for_management(
    activity_id: uuid.UUID,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> Activity:
    del current_user

    return get_activity(
        db,
        activity_id,
    )

@router.get(
    "/{activity_id}",
    response_model=ActivityResponse,
    summary="Get published activity",
)
def get_public_activity(
    activity_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> Activity:
    activity = get_activity(
        db,
        activity_id,
    )

    if activity.status != ActivityStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found.",
        )

    return activity


# ============================================================
# STAFF / ADMIN
# ============================================================


@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an activity",
)
def create_new_activity(
    data: ActivityCreateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> Activity:
    return create_activity(
        db,
        data,
        current_user.id,
    )


@router.patch(
    "/{activity_id}",
    response_model=ActivityResponse,
    summary="Update an activity",
)
def update_existing_activity(
    activity_id: uuid.UUID,
    data: ActivityUpdateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> Activity:
    del current_user

    return update_activity(
        db,
        activity_id,
        data,
    )


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an activity",
)
def delete_existing_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> None:
    del current_user

    delete_activity(
        db,
        activity_id,
    )