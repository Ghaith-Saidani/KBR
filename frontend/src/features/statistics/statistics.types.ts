export interface MemberStatistics {
  total: number;
  pending: number;
  active: number;
  suspended: number;
  inactive: number;
  archived: number;
}

export interface UserStatistics {
  total: number;
  members: number;
  staff: number;
  admins: number;
}

export interface EventStatistics {
  total: number;
  draft: number;
  published: number;
  cancelled: number;
  upcoming: number;
  past: number;
}

export interface ActivityStatistics {
  total: number;
  draft: number;
  published: number;
  upcoming: number;
  past: number;
}

export interface NewsStatistics {
  total: number;
  draft: number;
  published: number;
}

export interface StatisticsOverview {
  members: MemberStatistics;
  users: UserStatistics;
  events: EventStatistics;
  activities: ActivityStatistics;
  news: NewsStatistics;
}

export interface StatisticsTrendPoint {
  month: string;
  members: number;
  events: number;
  activities: number;
  news: number;
}

export interface StatisticsTrends {
  months: StatisticsTrendPoint[];
}