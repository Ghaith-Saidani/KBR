export type EventStatus =
  | "draft"
  | "published"
  | "cancelled";

export interface Event {
  id: string;
  title: string;
  description: string | null;
  location: string | null;
  start_at: string;
  end_at: string | null;
  cover_image: string | null;
  status: EventStatus;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface EventListResponse {
  items: Event[];
  total: number;
  skip: number;
  limit: number;
}

export interface EventListParams {
  search?: string;
  upcoming?: boolean;
  skip?: number;
  limit?: number;
}

export interface EventCreateRequest {
  title: string;
  description?: string | null;
  location?: string | null;
  start_at: string;
  end_at?: string | null;
  cover_image?: string | null;
  status?: EventStatus;
}

export interface EventUpdateRequest {
  title?: string;
  description?: string | null;
  location?: string | null;
  start_at?: string;
  end_at?: string | null;
  cover_image?: string | null;
  status?: EventStatus;
}