from datetime import datetime, timezone

from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from backend.app.models.activity import Activity, ActivityStatus
from backend.app.models.event import Event, EventStatus
from backend.app.models.member import Member, MemberStatus
from backend.app.models.news import News, NewsStatus
from backend.app.models.user import User, UserRole, UserStatus
from backend.app.schemas.statistics import (
    ActivityStatistics,
    EventStatistics,
    MemberStatistics,
    NewsStatistics,
    StatisticsOverviewResponse,
    StatisticsTrendPoint,
    StatisticsTrendsResponse,
    UserStatistics,
)


def get_statistics_overview(
    db: Session,
) -> StatisticsOverviewResponse:
    """
    Return the current global statistics for the KBR platform.
    """

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

    now = datetime.now(timezone.utc)

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

    return StatisticsOverviewResponse(
        members=MemberStatistics(
            total=total_members,
            pending=pending_members,
            active=active_members,
            suspended=suspended_members,
            inactive=inactive_members,
            archived=archived_members,
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
        ),
        activities=ActivityStatistics(
            total=total_activities,
            draft=draft_activities,
            published=published_activities,
            upcoming=upcoming_activities,
            past=past_activities,
        ),
        news=NewsStatistics(
            total=total_news,
            draft=draft_news,
            published=published_news,
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