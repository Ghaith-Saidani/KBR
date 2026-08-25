export type NewsStatus =
  | "draft"
  | "published";

export interface News {
  id: string;
  title: string;
  slug: string;
  excerpt: string | null;
  content: string;
  cover_image: string | null;
  status: NewsStatus;
  published_at: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface NewsListResponse {
  items: News[];
  total: number;
  skip: number;
  limit: number;
}

export interface NewsListParams {
  search?: string;
  skip?: number;
  limit?: number;
}

export interface NewsCreateRequest {
  title: string;
  slug: string;
  excerpt?: string | null;
  content: string;
  cover_image?: string | null;
  status?: NewsStatus;
  published_at?: string | null;
}

export interface NewsUpdateRequest {
  title?: string;
  slug?: string;
  excerpt?: string | null;
  content?: string;
  cover_image?: string | null;
  status?: NewsStatus;
  published_at?: string | null;
}