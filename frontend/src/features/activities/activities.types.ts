export type ActivityStatus =
  | "draft"
  | "published";

export interface Activity {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  description: string;
  cover_image: string | null;
  status: ActivityStatus;
  start_at: string | null;
  end_at: string | null;
  location: string | null;
  published_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface ActivityListResponse {
  items: Activity[];
  total: number;
  skip: number;
  limit: number;
}

export interface ActivityListParams {
  skip?: number;
  limit?: number;
  search?: string;
}

export interface ActivityCreateRequest {
  title: string;
  slug: string;
  excerpt?: string | null;
  description: string;
  cover_image?: string | null;
  status?: ActivityStatus;
  start_at?: string | null;
  end_at?: string | null;
  location?: string | null;
  published_at?: string | null;
}

export interface ActivityUpdateRequest {
  title?: string;
  slug?: string;
  excerpt?: string | null;
  description?: string;
  cover_image?: string | null;
  status?: ActivityStatus;
  start_at?: string | null;
  end_at?: string | null;
  location?: string | null;
  published_at?: string | null;
}