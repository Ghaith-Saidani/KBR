import type {
  UserRole,
  UserStatus,
} from "../auth/auth.types";

export interface AdminIdentity {
  user_id: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  is_email_verified: boolean;
  created_at: string;
}

export interface AdminMember {
  user_id: string;
  member_id: string;

  email: string;

  first_name: string;
  last_name: string;

  phone: string | null;
  profile_image: string | null;
  bio: string | null;
  joined_at: string | null;

  role: UserRole;
  status: UserStatus;
  is_email_verified: boolean;

  created_at: string;
  updated_at: string;
}

export interface AdminMemberListResponse {
  items: AdminMember[];
  total: number;
  skip: number;
  limit: number;
}

export interface AdminMemberListParams {
  skip?: number;
  limit?: number;
  search?: string;
  role?: UserRole;
  status?: UserStatus;
}

export interface AdminMemberUpdateRequest {
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  profile_image?: string | null;
  bio?: string | null;
}

export interface AdminRoleUpdateRequest {
  role: UserRole;
}

export interface AdminMemberStats {
  total: number;
  pending: number;
  active: number;
  suspended: number;
}

export interface AdminUserStats {
  total: number;
  members: number;
  staff: number;
  admins: number;
}

export interface AdminDashboard {
  members: AdminMemberStats;
  users: AdminUserStats;
}