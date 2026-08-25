import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  activateAdminMember,
  getAdminDashboard,
  getAdminIdentity,
  getAdminMember,
  getAdminMembers,
  suspendAdminMember,
  updateAdminMember,
  updateAdminMemberRole,
} from "./admin.api";

import type {
  AdminMemberListParams,
  AdminMemberUpdateRequest,
  AdminRoleUpdateRequest,
} from "./admin.types";

export const adminKeys = {
  all: ["admin"] as const,

  identity: () =>
    [...adminKeys.all, "identity"] as const,

  dashboard: () =>
    [...adminKeys.all, "dashboard"] as const,

  members: () =>
    [...adminKeys.all, "members"] as const,

  memberList: (
    params: AdminMemberListParams,
  ) =>
    [
      ...adminKeys.members(),
      "list",
      params,
    ] as const,

  memberDetails: () =>
    [...adminKeys.members(), "detail"] as const,

  memberDetail: (
    memberId: string,
  ) =>
    [
      ...adminKeys.memberDetails(),
      memberId,
    ] as const,
};

export function useAdminIdentity() {
  return useQuery({
    queryKey: adminKeys.identity(),

    queryFn: getAdminIdentity,
  });
}

export function useAdminDashboard() {
  return useQuery({
    queryKey: adminKeys.dashboard(),

    queryFn: getAdminDashboard,
  });
}

export function useAdminMembers(
  params: AdminMemberListParams = {},
) {
  return useQuery({
    queryKey: adminKeys.memberList(params),

    queryFn: () =>
      getAdminMembers(params),

    placeholderData:
      keepPreviousData,
  });
}

export function useAdminMember(
  memberId: string | undefined,
) {
  return useQuery({
    queryKey: adminKeys.memberDetail(
      memberId ?? "",
    ),

    queryFn: () =>
      getAdminMember(memberId!),

    enabled:
      Boolean(memberId),
  });
}

export function useUpdateAdminMember() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      memberId,
      data,
    }: {
      memberId: string;
      data: AdminMemberUpdateRequest;
    }) =>
      updateAdminMember(
        memberId,
        data,
      ),

    onSuccess: (
      updatedMember,
    ) => {
      queryClient.setQueryData(
        adminKeys.memberDetail(
          updatedMember.member_id,
        ),
        updatedMember,
      );

      queryClient.invalidateQueries({
        queryKey: adminKeys.members(),
      });

      queryClient.invalidateQueries({
        queryKey: adminKeys.dashboard(),
      });
    },
  });
}

export function useActivateAdminMember() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      memberId: string,
    ) =>
      activateAdminMember(
        memberId,
      ),

    onSuccess: (
      updatedMember,
    ) => {
      queryClient.setQueryData(
        adminKeys.memberDetail(
          updatedMember.member_id,
        ),
        updatedMember,
      );

      queryClient.invalidateQueries({
        queryKey: adminKeys.members(),
      });

      queryClient.invalidateQueries({
        queryKey: adminKeys.dashboard(),
      });
    },
  });
}

export function useSuspendAdminMember() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      memberId: string,
    ) =>
      suspendAdminMember(
        memberId,
      ),

    onSuccess: (
      updatedMember,
    ) => {
      queryClient.setQueryData(
        adminKeys.memberDetail(
          updatedMember.member_id,
        ),
        updatedMember,
      );

      queryClient.invalidateQueries({
        queryKey: adminKeys.members(),
      });

      queryClient.invalidateQueries({
        queryKey: adminKeys.dashboard(),
      });
    },
  });
}

export function useUpdateAdminMemberRole() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      memberId,
      data,
    }: {
      memberId: string;
      data: AdminRoleUpdateRequest;
    }) =>
      updateAdminMemberRole(
        memberId,
        data,
      ),

    onSuccess: (
      updatedMember,
    ) => {
      queryClient.setQueryData(
        adminKeys.memberDetail(
          updatedMember.member_id,
        ),
        updatedMember,
      );

      queryClient.invalidateQueries({
        queryKey: adminKeys.members(),
      });

      queryClient.invalidateQueries({
        queryKey: adminKeys.dashboard(),
      });
    },
  });
}