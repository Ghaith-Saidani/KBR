import api from "../../services/api";

import type {
  StatisticsOverview,
  StatisticsTrends,
} from "./statistics.types";

export async function getStatisticsOverview(): Promise<StatisticsOverview> {
  const response = await api.get<StatisticsOverview>(
    "/admin/statistics/overview",
  );

  return response.data;
}

export async function getStatisticsTrends(
  months = 6,
): Promise<StatisticsTrends> {
  const response = await api.get<StatisticsTrends>(
    "/admin/statistics/trends",
    {
      params: {
        months,
      },
    },
  );

  return response.data;
}