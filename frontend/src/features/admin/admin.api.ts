import api from "../../services/api";

import type {
  AdminDashboard,
  AdminIdentity,
  AdminMember,
  AdminMemberListParams,
  AdminMemberListResponse,
  AdminMemberUpdateRequest,
  AdminRoleUpdateRequest,
} from "./admin.types";

export async function getAdminIdentity(): Promise<AdminIdentity> {
  const response = await api.get<AdminIdentity>(
    "/admin/me",
  );

  return response.data;
}

export async function getAdminDashboard(): Promise<AdminDashboard> {
  const response = await api.get<AdminDashboard>(
    "/admin/dashboard",
  );

  return response.data;
}

export async function getAdminMembers(
  params: AdminMemberListParams = {},
): Promise<AdminMemberListResponse> {
  const response =
    await api.get<AdminMemberListResponse>(
      "/admin/members",
      {
        params,
      },
    );

  return response.data;
}

export async function getAdminMember(
  memberId: string,
): Promise<AdminMember> {
  const response =
    await api.get<AdminMember>(
      `/admin/members/${encodeURIComponent(memberId)}`,
    );

  return response.data;
}

export async function updateAdminMember(
  memberId: string,
  data: AdminMemberUpdateRequest,
): Promise<AdminMember> {
  const response =
    await api.patch<AdminMember>(
      `/admin/members/${encodeURIComponent(memberId)}`,
      data,
    );

  return response.data;
}

export async function activateAdminMember(
  memberId: string,
): Promise<AdminMember> {
  const response =
    await api.post<AdminMember>(
      `/admin/members/${encodeURIComponent(memberId)}/activate`,
    );

  return response.data;
}

export async function suspendAdminMember(
  memberId: string,
): Promise<AdminMember> {
  const response =
    await api.post<AdminMember>(
      `/admin/members/${encodeURIComponent(memberId)}/suspend`,
    );

  return response.data;
}

export async function updateAdminMemberRole(
  memberId: string,
  data: AdminRoleUpdateRequest,
): Promise<AdminMember> {
  const response =
    await api.patch<AdminMember>(
      `/admin/members/${encodeURIComponent(memberId)}/role`,
      data,
    );

  return response.data;
}