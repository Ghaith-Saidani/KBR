import uuid
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.activity import Activity, ActivityStatus
from backend.app.schemas.activity import (
    ActivityCreateRequest,
    ActivityUpdateRequest,
)


def create_activity(
    db: Session,
    data: ActivityCreateRequest,
    created_by: uuid.UUID,
) -> Activity:
    """
    Create a new activity.
    """

    existing_activity = (
        db.query(Activity)
        .filter(Activity.slug == data.slug)
        .first()
    )

    if existing_activity is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An activity with this slug already exists.",
        )

    activity = Activity(
        id=uuid.uuid4(),
        title=data.title,
        slug=data.slug,
        excerpt=data.excerpt,
        description=data.description,
        cover_image=data.cover_image,
        status=data.status,
        start_at=data.start_at,
        end_at=data.end_at,
        location=data.location,
        published_at=data.published_at,
        created_by=created_by,
    )

    db.add(activity)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An activity with this slug already exists.",
        )

    db.refresh(activity)

    return activity


def get_activity(
    db: Session,
    activity_id: uuid.UUID,
) -> Activity:
    """
    Retrieve an activity by ID.
    """

    activity = (
        db.query(Activity)
        .filter(Activity.id == activity_id)
        .first()
    )

    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found.",
        )

    return activity


def get_activity_by_slug(
    db: Session,
    slug: str,
) -> Activity:
    """
    Retrieve an activity by slug.
    """

    activity = (
        db.query(Activity)
        .filter(Activity.slug == slug)
        .first()
    )

    if activity is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Activity not found.",
        )

    return activity


def list_activities(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 50,
    include_unpublished: bool = False,
    search: str | None = None,
) -> tuple[list[Activity], int]:
    """
    List activities with pagination and optional search.
    """

    query = db.query(Activity)

    if not include_unpublished:
        query = query.filter(
            Activity.status == ActivityStatus.PUBLISHED
        )

    if search:
        search_pattern = f"%{search.strip()}%"

        query = query.filter(
            or_(
                Activity.title.ilike(search_pattern),
                Activity.excerpt.ilike(search_pattern),
                Activity.description.ilike(search_pattern),
            )
        )

    total = query.count()

    query = query.order_by(
        Activity.published_at.desc().nullslast(),
        Activity.created_at.desc(),
    )

    activities = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )

    return activities, total


def update_activity(
    db: Session,
    activity_id: uuid.UUID,
    data: ActivityUpdateRequest,
) -> Activity:
    """
    Update an existing activity.
    """

    activity = get_activity(
        db,
        activity_id,
    )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if "slug" in update_data:
        new_slug = update_data["slug"]

        if new_slug != activity.slug:
            existing_activity = (
                db.query(Activity)
                .filter(
                    Activity.slug == new_slug,
                    Activity.id != activity.id,
                )
                .first()
            )

            if existing_activity is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="An activity with this slug already exists.",
                )

    for field, value in update_data.items():
        setattr(
            activity,
            field,
            value,
        )

    if activity.status == ActivityStatus.PUBLISHED:
        if activity.published_at is None:
            activity.published_at = datetime.now().astimezone()

    elif activity.status == ActivityStatus.DRAFT:
        activity.published_at = None

    if (
        activity.start_at is not None
        and activity.end_at is not None
        and activity.end_at < activity.start_at
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_at cannot be earlier than start_at.",
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An activity with this slug already exists.",
        )

    db.refresh(activity)

    return activity


def delete_activity(
    db: Session,
    activity_id: uuid.UUID,
) -> None:
    """
    Permanently delete an activity.
    """

    activity = get_activity(
        db,
        activity_id,
    )

    db.delete(activity)
    db.commit()
