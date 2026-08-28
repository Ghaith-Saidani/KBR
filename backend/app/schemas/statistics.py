from pydantic import BaseModel


class MemberStatistics(BaseModel):
    total: int
    pending: int
    active: int
    suspended: int
    inactive: int
    archived: int


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


class ActivityStatistics(BaseModel):
    total: int
    draft: int
    published: int
    upcoming: int
    past: int


class NewsStatistics(BaseModel):
    total: int
    draft: int
    published: int


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