export type MemberStatus =
  | "active"
  | "inactive"
  | "archived";

export interface PublicMember {
  id: string;
  first_name: string;
  last_name: string;
  slug: string;
  position: string | null;
  profile_image: string | null;
  bio: string | null;
  joined_at: string | null;
  status: MemberStatus;
  created_at: string;
  updated_at: string;
}

export interface MemberListResponse {
  items: PublicMember[];
  total: number;
  skip: number;
  limit: number;
}

export interface MemberListParams {
  search?: string;
  status?: MemberStatus;
  skip?: number;
  limit?: number;
}