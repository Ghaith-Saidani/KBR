import api from "../../services/api";

import type {
  Notification,
  NotificationListParams,
  NotificationListResponse,
  NotificationReadAllResponse,
  NotificationReadResponse,
  NotificationUnreadCountResponse,
} from "./notifications.types";

export async function getNotifications(
  params: NotificationListParams = {},
): Promise<NotificationListResponse> {
  const response =
    await api.get<NotificationListResponse>(
      "/notifications",
      {
        params,
      },
    );

  return response.data;
}

export async function getUnreadNotificationCount(): Promise<number> {
  const response =
    await api.get<NotificationUnreadCountResponse>(
      "/notifications/unread-count",
    );

  return response.data.unread_count;
}

export async function markNotificationAsRead(
  notificationId: string,
): Promise<Notification> {
  const response =
    await api.patch<NotificationReadResponse>(
      `/notifications/${encodeURIComponent(
        notificationId,
      )}/read`,
    );

  return response.data.notification;
}

export async function markAllNotificationsAsRead(): Promise<NotificationReadAllResponse> {
  const response =
    await api.post<NotificationReadAllResponse>(
      "/notifications/read-all",
    );

  return response.data;
}