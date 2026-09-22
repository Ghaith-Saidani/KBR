import api from "../../services/api";

import type {
  AnalyticsQueryRequest,
  AnalyticsQueryResponse,
} from "./analytics.types";

export async function queryAnalytics(
  query: string,
): Promise<AnalyticsQueryResponse> {
  const payload: AnalyticsQueryRequest = {
    query,
  };

  const response =
    await api.post<AnalyticsQueryResponse>(
      "/admin/analytics/query",
      payload,
    );

  return response.data;
}