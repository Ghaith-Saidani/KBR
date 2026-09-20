import { useQuery } from "@tanstack/react-query";

import { getActivityLogs } from "./adminActivity.api";

import type {
  ActivityLogFilters,
} from "./adminActivity.types";

export const adminActivityKeys = {
  all: [
    "admin",
    "activity-logs",
  ] as const,

  list: (
    filters: ActivityLogFilters,
  ) => [
    ...adminActivityKeys.all,
    "list",
    filters,
  ] as const,
};

export function useAdminActivityLogs(
  filters: ActivityLogFilters,
) {
  return useQuery({
    queryKey:
      adminActivityKeys.list(filters),

    queryFn: () =>
      getActivityLogs(filters),

    placeholderData: (
      previousData,
    ) => previousData,
  });
}