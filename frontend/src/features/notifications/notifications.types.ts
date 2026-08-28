export type NotificationType =
  | "info"
  | "success"
  | "warning"
  | "error";

export interface Notification {
  id: string;
  user_id: string;
  type: NotificationType;
  title: string;
  message: string;
  is_read: boolean;
  read_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
  skip: number;
  limit: number;
  unread_count: number;
}

export interface NotificationUnreadCountResponse {
  unread_count: number;
}

export interface NotificationReadResponse {
  message: string;
  notification: Notification;
}

export interface NotificationReadAllResponse {
  message: string;
  updated_count: number;
}

export interface NotificationListParams {
  skip?: number;
  limit?: number;
  unread_only?: boolean;
}