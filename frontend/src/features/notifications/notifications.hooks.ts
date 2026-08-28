import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getNotifications,
  getUnreadNotificationCount,
  markAllNotificationsAsRead,
  markNotificationAsRead,
} from "./notifications.api";

import type {
  NotificationListParams,
} from "./notifications.types";

export const notificationKeys = {
  all: ["notifications"] as const,

  lists: () =>
    [...notificationKeys.all, "list"] as const,

  list: (
    params: NotificationListParams,
  ) =>
    [
      ...notificationKeys.lists(),
      params,
    ] as const,

  unreadCount: () =>
    [
      ...notificationKeys.all,
      "unread-count",
    ] as const,
};

export function useNotifications(
  params: NotificationListParams = {},
) {
  return useQuery({
    queryKey:
      notificationKeys.list(params),

    queryFn: () =>
      getNotifications(params),

    placeholderData:
      keepPreviousData,
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey:
      notificationKeys.unreadCount(),

    queryFn:
      getUnreadNotificationCount,
  });
}

export function useMarkNotificationAsRead() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      notificationId: string,
    ) =>
      markNotificationAsRead(
        notificationId,
      ),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey:
          notificationKeys.all,
      });
    },
  });
}

export function useMarkAllNotificationsAsRead() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn:
      markAllNotificationsAsRead,

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey:
          notificationKeys.all,
      });
    },
  });
}