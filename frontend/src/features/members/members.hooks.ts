import {
  keepPreviousData,
  useQuery,
} from "@tanstack/react-query";

import {
  getMemberById,
  getMemberBySlug,
  getMembers,
} from "./members.api";

import type {
  MemberListParams,
} from "./members.types";

export const memberKeys = {
  all: ["members"] as const,

  lists: () =>
    [...memberKeys.all, "list"] as const,

  list: (params: MemberListParams) =>
    [...memberKeys.lists(), params] as const,

  details: () =>
    [...memberKeys.all, "detail"] as const,

  detail: (slug: string) =>
    [...memberKeys.details(), slug] as const,
};

export function useMembers(
  params: MemberListParams = {},
) {
  return useQuery({
    queryKey: memberKeys.list(params),
    queryFn: () => getMembers(params),
    placeholderData: keepPreviousData,
  });
}

export function useMemberBySlug(
  slug: string | undefined,
) {
  return useQuery({
    queryKey: memberKeys.detail(slug ?? ""),
    queryFn: () => getMemberBySlug(slug!),
    enabled: Boolean(slug),
  });
}

export function useMemberById(
  memberId: string | undefined,
) {
  return useQuery({
    queryKey: [
      ...memberKeys.details(),
      "id",
      memberId ?? "",
    ],
    queryFn: () => getMemberById(memberId!),
    enabled: Boolean(memberId),
  });
}