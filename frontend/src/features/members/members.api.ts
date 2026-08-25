import api from "../../services/api";

import type {
  MemberListParams,
  MemberListResponse,
  MemberProfile,
  MemberUpdateRequest,
  PublicMember,
} from "./members.types";

export async function getMembers(
  params: MemberListParams = {},
): Promise<MemberListResponse> {
  const response = await api.get<MemberListResponse>(
    "/members",
    {
      params,
    },
  );

  return response.data;
}

export async function getMemberBySlug(
  slug: string,
): Promise<PublicMember> {
  const response = await api.get<PublicMember>(
    `/members/slug/${encodeURIComponent(slug)}`,
  );

  return response.data;
}

export async function getMemberById(
  memberId: string,
): Promise<PublicMember> {
  const response = await api.get<PublicMember>(
    `/members/${memberId}`,
  );

  return response.data;
}

export async function getMyMemberProfile(): Promise<MemberProfile> {
  const response = await api.get<MemberProfile>(
    "/members/me",
  );

  return response.data;
}

export async function updateMyMemberProfile(
  data: MemberUpdateRequest,
): Promise<MemberProfile> {
  const response = await api.patch<MemberProfile>(
    "/members/me",
    data,
  );

  return response.data;
}