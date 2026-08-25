import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.api.auth import get_current_user
from backend.app.core.database import get_db
from backend.app.core.permissions import require_staff
from backend.app.models.news import News, NewsStatus
from backend.app.models.user import User
from backend.app.schemas.news import (
    NewsCreateRequest,
    NewsListResponse,
    NewsResponse,
    NewsUpdateRequest,
)
from backend.app.services.news import (
    create_news,
    delete_news,
    get_news,
    get_news_by_slug,
    list_news,
    update_news,
)


router = APIRouter(
    prefix="/news",
    tags=["news"],
)


@router.get(
    "",
    response_model=NewsListResponse,
    summary="List published news",
    description=(
        "Return published news articles visible to the public. "
        "Results can be searched and paginated."
    ),
)
def get_news_articles(
    skip: int = Query(
        default=0,
        ge=0,
        description="Number of articles to skip.",
    ),
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
        description="Maximum number of articles to return.",
    ),
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
        description="Search title, excerpt, or content.",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> NewsListResponse:
    items, total = list_news(
        db,
        skip=skip,
        limit=limit,
        include_unpublished=False,
        search=search,
    )

    return NewsListResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/slug/{slug}",
    response_model=NewsResponse,
    summary="Get published news by slug",
    description="Return a single published news article by its slug.",
    responses={
        404: {
            "description": "News article not found.",
        },
    },
)
def get_news_by_slug_endpoint(
    slug: str,
    db: Session = Depends(get_db),
) -> News:
    news = get_news_by_slug(
        db,
        slug,
    )

    if news.status != NewsStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News article not found.",
        )

    return news


@router.get(
    "/{news_id}",
    response_model=NewsResponse,
    summary="Get published news article",
    description="Return a single published news article.",
    responses={
        404: {
            "description": "News article not found.",
        },
    },
)
def get_news_details(
    news_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> News:
    news = get_news(
        db,
        news_id,
    )

    if news.status != NewsStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News article not found.",
        )

    return news


@router.post(
    "",
    response_model=NewsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a news article",
    description=(
        "Create a news article. "
        "Staff members and administrators can create articles."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        403: {
            "description": "Staff privileges required.",
        },
        422: {
            "description": "Invalid news article data.",
        },
    },
)
def create_new_article(
    data: NewsCreateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> News:
    return create_news(
        db,
        data,
        current_user.id,
    )


@router.patch(
    "/{news_id}",
    response_model=NewsResponse,
    summary="Update a news article",
    description=(
        "Update an existing news article. "
        "Only provided fields are modified."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        403: {
            "description": "Staff privileges required.",
        },
        404: {
            "description": "News article not found.",
        },
        422: {
            "description": "Invalid news article data.",
        },
    },
)
def update_existing_article(
    news_id: uuid.UUID,
    data: NewsUpdateRequest,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> News:
    return update_news(
        db,
        news_id,
        data,
    )


@router.delete(
    "/{news_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a news article",
    description=(
        "Permanently delete a news article. "
        "Only staff members and administrators can delete articles."
    ),
    responses={
        401: {
            "description": "Authentication required.",
        },
        403: {
            "description": "Staff privileges required.",
        },
        404: {
            "description": "News article not found.",
        },
    },
)
def delete_existing_article(
    news_id: uuid.UUID,
    current_user: User = Depends(require_staff),
    db: Session = Depends(get_db),
) -> None:
    delete_news(
        db,
        news_id,
    )