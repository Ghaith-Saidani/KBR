import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  getMemberById,
  getMemberBySlug,
  getMembers,
  getMyMemberProfile,
  updateMyMemberProfile,
} from "./members.api";

import type {
  MemberListParams,
  MemberUpdateRequest,
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

  me: () =>
    [...memberKeys.all, "me"] as const,
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

export function useMyMemberProfile(
  enabled = true,
) {
  return useQuery({
    queryKey: memberKeys.me(),
    queryFn: getMyMemberProfile,
    enabled,
    retry: false,
  });
}

export function useUpdateMyMemberProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (
      data: MemberUpdateRequest,
    ) => updateMyMemberProfile(data),

    onSuccess: async (updatedMember) => {
      queryClient.setQueryData(
        memberKeys.me(),
        updatedMember,
      );

      await queryClient.invalidateQueries({
        queryKey: memberKeys.lists(),
      });

      await queryClient.invalidateQueries({
        queryKey: memberKeys.details(),
      });
    },
  });
}