import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
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


@router.get(
    "",
    response_model=ActivityListResponse,
    summary="List published activities",
    description=(
        "Return published activities visible to authenticated users. "
        "Results can be searched and paginated."
    ),
)
def get_activities(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of activities to skip.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of activities to return.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search title, excerpt, or description.",
    ),
    current_user: User = Depends(get_current_user),
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
    "/slug/{slug}",
    response_model=ActivityResponse,
    summary="Get published activity by slug",
    description="Return a single published activity by its slug.",
)
def get_activity_by_slug_endpoint(
    slug: str,
    current_user: User = Depends(get_current_user),
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
    "/{activity_id}",
    response_model=ActivityResponse,
    summary="Get published activity",
    description="Return a single published activity.",
)
def get_activity_details(
    activity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
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


@router.post(
    "",
    response_model=ActivityResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an activity",
    description=(
        "Create an activity. "
        "Staff members and administrators can create activities."
    ),
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
    description=(
        "Update an existing activity. "
        "Only provided fields are modified."
    ),
)
def update_existing_activity(
    activity_id: uuid.UUID,
    data: ActivityUpdateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> Activity:
    return update_activity(
        db,
        activity_id,
        data,
    )


@router.delete(
    "/{activity_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an activity",
    description=(
        "Permanently delete an activity. "
        "Only staff members and administrators can delete activities."
    ),
)
def delete_existing_activity(
    activity_id: uuid.UUID,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> None:
    delete_activity(
        db,
        activity_id,
    )
