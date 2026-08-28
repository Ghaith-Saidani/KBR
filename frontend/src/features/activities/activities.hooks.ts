import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createActivity,
  deleteActivity,
  getActivities,
  getActivityById,
  getActivityBySlug,
  getManageActivities,
  updateActivity,
} from "./activities.api";

import type {
  ActivityCreateRequest,
  ActivityListParams,
  ActivityUpdateRequest,
} from "./activities.types";

const activitiesKeys = {
  all: ["activities"] as const,

  lists: () =>
    [...activitiesKeys.all, "list"] as const,

  list: (
    params?: ActivityListParams,
  ) =>
    [
      ...activitiesKeys.lists(),
      params,
    ] as const,

  manageLists: () =>
    [...activitiesKeys.all, "manage-list"] as const,

  manageList: (
    params?: ActivityListParams,
  ) =>
    [
      ...activitiesKeys.manageLists(),
      params,
    ] as const,

  details: () =>
    [...activitiesKeys.all, "detail"] as const,

  detail: (id: string) =>
    [
      ...activitiesKeys.details(),
      id,
    ] as const,

  slug: (slug: string) =>
    [
      ...activitiesKeys.all,
      "slug",
      slug,
    ] as const,
};


export function useActivities(
  params?: ActivityListParams,
) {
  return useQuery({
    queryKey: activitiesKeys.list(params),

    queryFn: () =>
      getActivities(params),
  });
}


export function useManageActivities(
  params?: ActivityListParams,
) {
  return useQuery({
    queryKey:
      activitiesKeys.manageList(params),

    queryFn: () =>
      getManageActivities(params),
  });
}


export function useActivity(
  activityId?: string,
) {
  return useQuery({
    queryKey: activityId
      ? activitiesKeys.detail(activityId)
      : activitiesKeys.all,

    queryFn: () =>
      getActivityById(
        activityId as string,
      ),

    enabled: Boolean(activityId),
  });
}


export function useActivityBySlug(
  slug?: string,
) {
  return useQuery({
    queryKey: slug
      ? activitiesKeys.slug(slug)
      : activitiesKeys.all,

    queryFn: () =>
      getActivityBySlug(
        slug as string,
      ),

    enabled: Boolean(slug),
  });
}


export function useCreateActivity() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      data: ActivityCreateRequest,
    ) =>
      createActivity(data),

    onSuccess: (createdActivity) => {
      queryClient.invalidateQueries({
        queryKey: activitiesKeys.all,
      });

      queryClient.setQueryData(
        activitiesKeys.detail(
          createdActivity.id,
        ),
        createdActivity,
      );
    },
  });
}


export function useUpdateActivity() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      activityId,
      data,
    }: {
      activityId: string;
      data: ActivityUpdateRequest;
    }) =>
      updateActivity(
        activityId,
        data,
      ),

    onSuccess: (updatedActivity) => {
      queryClient.invalidateQueries({
        queryKey: activitiesKeys.all,
      });

      queryClient.setQueryData(
        activitiesKeys.detail(
          updatedActivity.id,
        ),
        updatedActivity,
      );

      queryClient.setQueryData(
        activitiesKeys.slug(
          updatedActivity.slug,
        ),
        updatedActivity,
      );
    },
  });
}


export function useDeleteActivity() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      activityId: string,
    ) =>
      deleteActivity(
        activityId,
      ),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: activitiesKeys.all,
      });
    },
  });
}