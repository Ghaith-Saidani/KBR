export interface UserActivity {
  id: string;
  user_id: string | null;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  method: string | null;
  endpoint: string | null;
  ip_address: string | null;
  user_agent: string | null;
  details: string | null;
  activity_metadata: Record<string, unknown> | null;
  occurred_at: string;
  created_at: string;
  updated_at: string;
}

export interface UserActivityListResponse {
  items: UserActivity[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export type ActivityType =
  | "business"
  | "technical";

export interface ActivityLogFilters {
  page?: number;
  page_size?: number;
  user_id?: string;
  action?: string;
  resource_type?: string;
  method?: string;
  activity_type?: ActivityType;
  date_from?: string;
  date_to?: string;
  sort_order?: "asc" | "desc";
}