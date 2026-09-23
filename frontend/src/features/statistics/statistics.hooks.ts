import { useQuery } from "@tanstack/react-query";

import {
  getRecentBusinessActivity,
  getStatisticsOverview,
  getStatisticsTrends,
} from "./statistics.api";

export const statisticsKeys = {
  all: ["statistics"] as const,

  overview: () =>
    [
      ...statisticsKeys.all,
      "overview",
    ] as const,

  trends: (
    months: number,
  ) =>
    [
      ...statisticsKeys.all,
      "trends",
      months,
    ] as const,

  recentActivity: (
    limit: number,
  ) =>
    [
      ...statisticsKeys.all,
      "recent-activity",
      limit,
    ] as const,
};

export function useStatisticsOverview() {
  return useQuery({
    queryKey:
      statisticsKeys.overview(),

    queryFn:
      getStatisticsOverview,
  });
}

export function useStatisticsTrends(
  months = 6,
) {
  return useQuery({
    queryKey:
      statisticsKeys.trends(months),

    queryFn: () =>
      getStatisticsTrends(months),
  });
}

export function useRecentBusinessActivity(
  limit = 10,
) {
  return useQuery({
    queryKey:
      statisticsKeys.recentActivity(limit),

    queryFn: () =>
      getRecentBusinessActivity(limit),
  });
}