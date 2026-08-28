import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.models.notification import NotificationType
from backend.app.services.notification import (
    add_notification_for_active_members,
)

from backend.app.models.news import News, NewsStatus
from backend.app.schemas.news import (
    NewsCreateRequest,
    NewsUpdateRequest,
)


def get_news(
    db: Session,
    news_id: uuid.UUID,
) -> News:
    """
    Retrieve a news article by ID.

    Raises 404 when the article does not exist.
    """

    news = db.get(News, news_id)

    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News article not found.",
        )

    return news


def get_news_by_slug(
    db: Session,
    slug: str,
) -> News:
    """
    Retrieve a news article by its unique slug.

    Raises 404 when the article does not exist.
    """

    normalized_slug = slug.strip().lower()

    news = db.scalar(
        select(News).where(
            News.slug == normalized_slug,
        )
    )

    if news is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="News article not found.",
        )

    return news


def list_news(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    include_unpublished: bool = False,
    search: str | None = None,
) -> tuple[list[News], int]:
    """
    Return news articles with optional filtering and pagination.

    Public callers only receive published articles.

    Published articles are ordered from newest to oldest.
    """

    filters = []

    if not include_unpublished:
        filters.append(
            News.status == NewsStatus.PUBLISHED,
        )

    if search:
        normalized_search = search.strip()

        if normalized_search:
            search_pattern = f"%{normalized_search}%"

            filters.append(
                or_(
                    News.title.ilike(search_pattern),
                    News.excerpt.ilike(search_pattern),
                    News.content.ilike(search_pattern),
                )
            )

    count_statement = select(
        func.count(News.id),
    )

    statement = select(News)

    if filters:
        count_statement = count_statement.where(
            *filters,
        )

        statement = statement.where(
            *filters,
        )

    total = db.scalar(
        count_statement,
    ) or 0

    statement = (
        statement
        .order_by(
            News.published_at.desc().nullslast(),
            News.created_at.desc(),
            News.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    items = list(
        db.scalars(statement).all(),
    )

    return items, total


def _check_slug_available(
    db: Session,
    slug: str,
    *,
    exclude_news_id: uuid.UUID | None = None,
) -> None:
    """
    Ensure that a slug is not already used by another article.

    Raises 409 when the slug is already taken.
    """

    statement = select(News.id).where(
        News.slug == slug,
    )

    if exclude_news_id is not None:
        statement = statement.where(
            News.id != exclude_news_id,
        )

    existing_id = db.scalar(statement)

    if existing_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A news article with this slug already exists.",
        )


def _normalize_publication_state(
    *,
    status_value: NewsStatus,
    published_at: datetime | None,
) -> datetime | None:
    """
    Normalize publication metadata according to article status.

    Published articles always have a publication timestamp.

    Draft articles do not have a publication timestamp.
    """

    if status_value == NewsStatus.PUBLISHED:
        return published_at or datetime.now(timezone.utc)

    return None


def create_news(
    db: Session,
    data: NewsCreateRequest,
    current_user_id: uuid.UUID,
) -> News:
    """
    Create a new news article.

    If the article is created directly as published,
    notify all active members.
    """

    slug = data.slug.strip().lower()

    _check_slug_available(
        db,
        slug,
    )

    published_at = _normalize_publication_state(
        status_value=data.status,
        published_at=data.published_at,
    )

    news = News(
        title=data.title,
        slug=slug,
        excerpt=data.excerpt,
        content=data.content,
        cover_image=data.cover_image,
        status=data.status,
        published_at=published_at,
        created_by=current_user_id,
    )

    db.add(news)

    if data.status == NewsStatus.PUBLISHED:
        add_notification_for_active_members(
            db,
            title="Nouvelle actualité",
            message=(
                f"Une nouvelle actualité KBR est disponible : "
                f"{data.title.strip()}."
            ),
            notification_type=NotificationType.INFO,
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A news article with this slug already exists.",
        )

    db.refresh(news)

    return news


def update_news(
    db: Session,
    news_id: uuid.UUID,
    data: NewsUpdateRequest,
) -> News:
    """
    Update an existing news article.

    Only fields explicitly provided by the client are modified.

    Publication metadata is normalized automatically.

    A notification is generated only when the article transitions
    from a non-published state to published.
    """

    news = get_news(
        db,
        news_id,
    )

    previous_status = news.status

    update_data = data.model_dump(
        exclude_unset=True,
    )

    if not update_data:
        return news

    if "slug" in update_data:
        new_slug = update_data["slug"].strip().lower()

        _check_slug_available(
            db,
            new_slug,
            exclude_news_id=news.id,
        )

        update_data["slug"] = new_slug

    final_status = update_data.get(
        "status",
        news.status,
    )

    final_published_at = update_data.get(
        "published_at",
        news.published_at,
    )

    if final_status == NewsStatus.PUBLISHED:
        if (
            "status" in update_data
            and update_data["status"] == NewsStatus.PUBLISHED
            and news.status != NewsStatus.PUBLISHED
            and "published_at" not in update_data
        ):
            final_published_at = datetime.now(
                timezone.utc,
            )

        elif final_published_at is None:
            final_published_at = datetime.now(
                timezone.utc,
            )

    else:
        final_published_at = None

    update_data["published_at"] = final_published_at

    for field, value in update_data.items():
        setattr(
            news,
            field,
            value,
        )

    became_published = (
        previous_status != NewsStatus.PUBLISHED
        and news.status == NewsStatus.PUBLISHED
    )

    if became_published:
        add_notification_for_active_members(
            db,
            title="Nouvelle actualité",
            message=(
                f"Une nouvelle actualité KBR est disponible : "
                f"{news.title.strip()}."
            ),
            notification_type=NotificationType.INFO,
        )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A news article with this slug already exists.",
        )

    db.refresh(news)

    return news


def delete_news(
    db: Session,
    news_id: uuid.UUID,
) -> None:
    """
    Permanently delete a news article.
    """

    news = get_news(
        db,
        news_id,
    )

    db.delete(news)
    db.commit()