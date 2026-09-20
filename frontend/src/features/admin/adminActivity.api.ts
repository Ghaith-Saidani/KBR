import api from "../../services/api";

import type {
  ActivityLogFilters,
  UserActivityListResponse,
} from "./adminActivity.types";

export async function getActivityLogs(
  filters: ActivityLogFilters = {},
): Promise<UserActivityListResponse> {
  const params = new URLSearchParams();

  if (filters.page !== undefined) {
    params.set(
      "page",
      String(filters.page),
    );
  }

  if (filters.page_size !== undefined) {
    params.set(
      "page_size",
      String(filters.page_size),
    );
  }

  if (filters.user_id) {
    params.set(
      "user_id",
      filters.user_id,
    );
  }

  if (filters.action) {
    params.set(
      "action",
      filters.action,
    );
  }

  if (filters.resource_type) {
    params.set(
      "resource_type",
      filters.resource_type,
    );
  }

  if (filters.method) {
    params.set(
      "method",
      filters.method,
    );
  }

  if (filters.activity_type) {
    params.set(
      "activity_type",
      filters.activity_type,
    );
  }

  if (filters.date_from) {
    params.set(
      "date_from",
      filters.date_from,
    );
  }

  if (filters.date_to) {
    params.set(
      "date_to",
      filters.date_to,
    );
  }

  if (filters.sort_order) {
    params.set(
      "sort_order",
      filters.sort_order,
    );
  }

  const query = params.toString();

  const response =
    await api.get<UserActivityListResponse>(
      `/admin/activity-logs${
        query ? `?${query}` : ""
      }`,
    );

  return response.data;
}