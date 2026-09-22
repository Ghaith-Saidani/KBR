import {
  useMutation,
} from "@tanstack/react-query";

import {
  queryAnalytics,
} from "./analytics.api";

export function useAnalyticsQuery() {
  return useMutation({
    mutationFn: (
      query: string,
    ) => queryAnalytics(query),
  });
}