import api from "../../services/api";

import type {
  Activity,
  ActivityCreateRequest,
  ActivityListParams,
  ActivityListResponse,
  ActivityUpdateRequest,
} from "./activities.types";

export async function getActivities(
  params?: ActivityListParams,
): Promise<ActivityListResponse> {
  const response =
    await api.get<ActivityListResponse>(
      "/activities",
      {
        params,
      },
    );

  return response.data;
}

export async function getActivityById(
  activityId: string,
): Promise<Activity> {
  const response =
    await api.get<Activity>(
      `/activities/${activityId}`,
    );

  return response.data;
}

export async function getActivityBySlug(
  slug: string,
): Promise<Activity> {
  const response =
    await api.get<Activity>(
      `/activities/slug/${slug}`,
    );

  return response.data;
}

export async function createActivity(
  data: ActivityCreateRequest,
): Promise<Activity> {
  const response =
    await api.post<Activity>(
      "/activities",
      data,
    );

  return response.data;
}

export async function updateActivity(
  activityId: string,
  data: ActivityUpdateRequest,
): Promise<Activity> {
  const response =
    await api.patch<Activity>(
      `/activities/${activityId}`,
      data,
    );

  return response.data;
}

export async function deleteActivity(
  activityId: string,
): Promise<void> {
  await api.delete(
    `/activities/${activityId}`,
  );
}