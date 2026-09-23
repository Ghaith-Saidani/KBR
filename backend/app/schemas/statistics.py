from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MemberStatistics(BaseModel):
    total: int
    pending: int
    active: int
    suspended: int
    inactive: int
    archived: int
    created_this_month: int
    created_last_month: int


class UserStatistics(BaseModel):
    total: int
    members: int
    staff: int
    admins: int


class EventStatistics(BaseModel):
    total: int
    draft: int
    published: int
    cancelled: int
    upcoming: int
    past: int
    created_this_month: int
    created_last_month: int


class ActivityStatistics(BaseModel):
    total: int
    draft: int
    published: int
    upcoming: int
    past: int
    created_this_month: int
    created_last_month: int


class NewsStatistics(BaseModel):
    total: int
    draft: int
    published: int
    created_this_month: int
    created_last_month: int


class StatisticsOverviewResponse(BaseModel):
    members: MemberStatistics
    users: UserStatistics
    events: EventStatistics
    activities: ActivityStatistics
    news: NewsStatistics


class StatisticsTrendPoint(BaseModel):
    month: str
    members: int
    events: int
    activities: int
    news: int


class StatisticsTrendsResponse(BaseModel):
    months: list[StatisticsTrendPoint]


class RecentBusinessActivity(BaseModel):
    id: UUID
    action: str
    resource_type: str | None = None
    resource_id: UUID | None = None
    details: str | None = None
    occurred_at: datetime
    user_id: UUID | None = None


class RecentBusinessActivityResponse(BaseModel):
    activities: list[RecentBusinessActivity]