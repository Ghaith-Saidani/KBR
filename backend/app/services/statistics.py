from datetime import datetime, timezone

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from backend.app.models.activity import Activity, ActivityStatus
from backend.app.models.event import Event, EventStatus
from backend.app.models.member import Member, MemberStatus
from backend.app.models.news import News, NewsStatus
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.models.user_activity import UserActivity
from backend.app.schemas.statistics import (
    ActivityStatistics,
    EventStatistics,
    MemberStatistics,
    NewsStatistics,
    RecentBusinessActivity,
    RecentBusinessActivityResponse,
    StatisticsOverviewResponse,
    StatisticsTrendPoint,
    StatisticsTrendsResponse,
    UserStatistics,
)


BUSINESS_AUDIT_ACTIONS = {
    "ACTIVITY_CREATED",
    "ACTIVITY_UPDATED",
    "ACTIVITY_PUBLISHED",
    "ACTIVITY_DELETED",
    "EVENT_CREATED",
    "EVENT_UPDATED",
    "EVENT_PUBLISHED",
    "EVENT_CANCELLED",
    "EVENT_DELETED",
    "NEWS_CREATED",
    "NEWS_UPDATED",
    "NEWS_PUBLISHED",
    "NEWS_UNPUBLISHED",
    "NEWS_DELETED",
    "MEMBER_UPDATED",
    "MEMBER_DEACTIVATED",
    "MEMBER_REACTIVATED",
    "MEMBER_ARCHIVED",
    "MEMBER_DELETED",
    "USER_ACTIVATED",
}


def get_month_boundaries(
    now: datetime,
) -> tuple[datetime, datetime, datetime]:
    """
    Return calendar-month boundaries.

    Returns:
        current_month_start:
            Beginning of the current month.

        next_month_start:
            Beginning of the next month.

        previous_month_start:
            Beginning of the previous month.
    """

    current_month_start = datetime(
        year=now.year,
        month=now.month,
        day=1,
        tzinfo=timezone.utc,
    )

    if now.month == 12:
        next_month_start = datetime(
            year=now.year + 1,
            month=1,
            day=1,
            tzinfo=timezone.utc,
        )
    else:
        next_month_start = datetime(
            year=now.year,
            month=now.month + 1,
            day=1,
            tzinfo=timezone.utc,
        )

    if now.month == 1:
        previous_month_start = datetime(
            year=now.year - 1,
            month=12,
            day=1,
            tzinfo=timezone.utc,
        )
    else:
        previous_month_start = datetime(
            year=now.year,
            month=now.month - 1,
            day=1,
            tzinfo=timezone.utc,
        )

    return (
        current_month_start,
        next_month_start,
        previous_month_start,
    )


def get_created_this_month_count(
    db: Session,
    model,
    current_month_start: datetime,
    next_month_start: datetime,
) -> int:
    """
    Count records created during the current calendar month.
    """

    return (
        db.scalar(
            select(func.count(model.id)).where(
                model.created_at >= current_month_start,
                model.created_at < next_month_start,
            )
        )
        or 0
    )


def get_created_last_month_count(
    db: Session,
    model,
    previous_month_start: datetime,
    current_month_start: datetime,
) -> int:
    """
    Count records created during the previous calendar month.
    """

    return (
        db.scalar(
            select(func.count(model.id)).where(
                model.created_at >= previous_month_start,
                model.created_at < current_month_start,
            )
        )
        or 0
    )


def get_statistics_overview(
    db: Session,
) -> StatisticsOverviewResponse:
    """
    Return the current global statistics for the KBR platform.

    In addition to the existing totals/status counters, this endpoint
    exposes current-month and previous-month creation counts for the
    main business entities.
    """

    # ------------------------------------------------------------------
    # Date boundaries
    # ------------------------------------------------------------------

    now = datetime.now(timezone.utc)

    (
        current_month_start,
        next_month_start,
        previous_month_start,
    ) = get_month_boundaries(now)

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------

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
                User.status == UserStatus.PENDING,
            )
        )
        or 0
    )

    active_members = (
        db.scalar(
            select(func.count(Member.id))
            .where(
                Member.status == MemberStatus.ACTIVE,
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
                User.status == UserStatus.SUSPENDED,
            )
        )
        or 0
    )

    inactive_members = (
        db.scalar(
            select(func.count(Member.id))
            .where(
                Member.status == MemberStatus.INACTIVE,
            )
        )
        or 0
    )

    archived_members = (
        db.scalar(
            select(func.count(Member.id))
            .where(
                Member.status == MemberStatus.ARCHIVED,
            )
        )
        or 0
    )

    members_created_this_month = get_created_this_month_count(
        db,
        Member,
        current_month_start,
        next_month_start,
    )

    members_created_last_month = get_created_last_month_count(
        db,
        Member,
        previous_month_start,
        current_month_start,
    )

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------

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
                User.role == UserRole.MEMBER,
            )
        )
        or 0
    )

    staff_users = (
        db.scalar(
            select(func.count(User.id))
            .where(
                User.role == UserRole.STAFF,
            )
        )
        or 0
    )

    admin_users = (
        db.scalar(
            select(func.count(User.id))
            .where(
                User.role == UserRole.ADMIN,
            )
        )
        or 0
    )

    # ------------------------------------------------------------------
    # Events
    # ------------------------------------------------------------------

    total_events = (
        db.scalar(
            select(func.count(Event.id))
        )
        or 0
    )

    draft_events = (
        db.scalar(
            select(func.count(Event.id))
            .where(
                Event.status == EventStatus.DRAFT,
            )
        )
        or 0
    )

    published_events = (
        db.scalar(
            select(func.count(Event.id))
            .where(
                Event.status == EventStatus.PUBLISHED,
            )
        )
        or 0
    )

    cancelled_events = (
        db.scalar(
            select(func.count(Event.id))
            .where(
                Event.status == EventStatus.CANCELLED,
            )
        )
        or 0
    )

    upcoming_events = (
        db.scalar(
            select(func.count(Event.id))
            .where(
                Event.start_at >= now,
                Event.status == EventStatus.PUBLISHED,
            )
        )
        or 0
    )

    past_events = (
        db.scalar(
            select(func.count(Event.id))
            .where(
                Event.start_at < now,
            )
        )
        or 0
    )

    events_created_this_month = get_created_this_month_count(
        db,
        Event,
        current_month_start,
        next_month_start,
    )

    events_created_last_month = get_created_last_month_count(
        db,
        Event,
        previous_month_start,
        current_month_start,
    )

    # ------------------------------------------------------------------
    # Activities
    # ------------------------------------------------------------------

    total_activities = (
        db.scalar(
            select(func.count(Activity.id))
        )
        or 0
    )

    draft_activities = (
        db.scalar(
            select(func.count(Activity.id))
            .where(
                Activity.status == ActivityStatus.DRAFT,
            )
        )
        or 0
    )

    published_activities = (
        db.scalar(
            select(func.count(Activity.id))
            .where(
                Activity.status == ActivityStatus.PUBLISHED,
            )
        )
        or 0
    )

    upcoming_activities = (
        db.scalar(
            select(func.count(Activity.id))
            .where(
                Activity.start_at >= now,
                Activity.status == ActivityStatus.PUBLISHED,
            )
        )
        or 0
    )

    past_activities = (
        db.scalar(
            select(func.count(Activity.id))
            .where(
                Activity.start_at < now,
            )
        )
        or 0
    )

    activities_created_this_month = get_created_this_month_count(
        db,
        Activity,
        current_month_start,
        next_month_start,
    )

    activities_created_last_month = get_created_last_month_count(
        db,
        Activity,
        previous_month_start,
        current_month_start,
    )

    # ------------------------------------------------------------------
    # News
    # ------------------------------------------------------------------

    total_news = (
        db.scalar(
            select(func.count(News.id))
        )
        or 0
    )

    draft_news = (
        db.scalar(
            select(func.count(News.id))
            .where(
                News.status == NewsStatus.DRAFT,
            )
        )
        or 0
    )

    published_news = (
        db.scalar(
            select(func.count(News.id))
            .where(
                News.status == NewsStatus.PUBLISHED,
            )
        )
        or 0
    )

    news_created_this_month = get_created_this_month_count(
        db,
        News,
        current_month_start,
        next_month_start,
    )

    news_created_last_month = get_created_last_month_count(
        db,
        News,
        previous_month_start,
        current_month_start,
    )

    # ------------------------------------------------------------------
    # Response
    # ------------------------------------------------------------------

    return StatisticsOverviewResponse(
        members=MemberStatistics(
            total=total_members,
            pending=pending_members,
            active=active_members,
            suspended=suspended_members,
            inactive=inactive_members,
            archived=archived_members,
            created_this_month=members_created_this_month,
            created_last_month=members_created_last_month,
        ),
        users=UserStatistics(
            total=total_users,
            members=member_users,
            staff=staff_users,
            admins=admin_users,
        ),
        events=EventStatistics(
            total=total_events,
            draft=draft_events,
            published=published_events,
            cancelled=cancelled_events,
            upcoming=upcoming_events,
            past=past_events,
            created_this_month=events_created_this_month,
            created_last_month=events_created_last_month,
        ),
        activities=ActivityStatistics(
            total=total_activities,
            draft=draft_activities,
            published=published_activities,
            upcoming=upcoming_activities,
            past=past_activities,
            created_this_month=activities_created_this_month,
            created_last_month=activities_created_last_month,
        ),
        news=NewsStatistics(
            total=total_news,
            draft=draft_news,
            published=published_news,
            created_this_month=news_created_this_month,
            created_last_month=news_created_last_month,
        ),
    )


def get_statistics_trends(
    db: Session,
    months: int = 6,
) -> StatisticsTrendsResponse:
    """
    Return monthly content/member creation statistics.

    The result contains the requested number of calendar months,
    including the current month.
    """

    now = datetime.now(timezone.utc)

    current_year = now.year
    current_month = now.month

    month_values: list[tuple[int, int]] = []

    for offset in range(months - 1, -1, -1):
        month_index = current_month - offset
        year = current_year

        while month_index <= 0:
            month_index += 12
            year -= 1

        month_values.append(
            (
                year,
                month_index,
            )
        )

    points: list[StatisticsTrendPoint] = []

    for year, month in month_values:
        members_count = (
            db.scalar(
                select(func.count(Member.id))
                .where(
                    extract(
                        "year",
                        Member.created_at,
                    )
                    == year,
                    extract(
                        "month",
                        Member.created_at,
                    )
                    == month,
                )
            )
            or 0
        )

        events_count = (
            db.scalar(
                select(func.count(Event.id))
                .where(
                    extract(
                        "year",
                        Event.created_at,
                    )
                    == year,
                    extract(
                        "month",
                        Event.created_at,
                    )
                    == month,
                )
            )
            or 0
        )

        activities_count = (
            db.scalar(
                select(func.count(Activity.id))
                .where(
                    extract(
                        "year",
                        Activity.created_at,
                    )
                    == year,
                    extract(
                        "month",
                        Activity.created_at,
                    )
                    == month,
                )
            )
            or 0
        )

        news_count = (
            db.scalar(
                select(func.count(News.id))
                .where(
                    extract(
                        "year",
                        News.created_at,
                    )
                    == year,
                    extract(
                        "month",
                        News.created_at,
                    )
                    == month,
                )
            )
            or 0
        )

        points.append(
            StatisticsTrendPoint(
                month=f"{year:04d}-{month:02d}",
                members=members_count,
                events=events_count,
                activities=activities_count,
                news=news_count,
            )
        )

    return StatisticsTrendsResponse(
        months=points,
    )


def get_recent_business_activity(
    db: Session,
    limit: int = 10,
) -> RecentBusinessActivityResponse:
    """
    Return the latest semantic business audit events.

    Technical HTTP activity is intentionally excluded. This endpoint
    is intended for the executive/admin dashboard and therefore only
    exposes meaningful business actions.
    """

    safe_limit = max(1, min(limit, 50))

    activities = (
        db.scalars(
            select(UserActivity)
            .where(
                UserActivity.action.in_(BUSINESS_AUDIT_ACTIONS),
            )
            .order_by(
                UserActivity.occurred_at.desc(),
            )
            .limit(safe_limit)
        )
        .all()
    )

    return RecentBusinessActivityResponse(
        activities=[
            RecentBusinessActivity(
                id=activity.id,
                action=activity.action,
                resource_type=activity.resource_type,
                resource_id=activity.resource_id,
                details=activity.details,
                occurred_at=activity.occurred_at,
                user_id=activity.user_id,
            )
            for activity in activities
        ],
    )