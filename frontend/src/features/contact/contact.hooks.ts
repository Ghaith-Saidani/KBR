import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  deleteContactMessage,
  getAdminContactMessage,
  getAdminContactMessages,
  submitContactMessage,
  updateContactMessageStatus,
} from "./contact.api";

import type {
  ContactMessageCreateRequest,
  ContactMessageListParams,
  ContactMessageStatus,
} from "./contact.types";

export const contactKeys = {
  all: ["contact"] as const,

  messages: () =>
    [...contactKeys.all, "messages"] as const,

  messageList: (
    params: ContactMessageListParams,
  ) =>
    [
      ...contactKeys.messages(),
      "list",
      params,
    ] as const,

  messageDetails: () =>
    [...contactKeys.messages(), "detail"] as const,

  messageDetail: (
    messageId: string,
  ) =>
    [
      ...contactKeys.messageDetails(),
      messageId,
    ] as const,
};

export function useSubmitContactMessage() {
  return useMutation({
    mutationFn: (
      data: ContactMessageCreateRequest,
    ) =>
      submitContactMessage(data),
  });
}

export function useAdminContactMessages(
  params: ContactMessageListParams = {},
) {
  return useQuery({
    queryKey:
      contactKeys.messageList(params),

    queryFn: () =>
      getAdminContactMessages(params),

    placeholderData:
      keepPreviousData,
  });
}

export function useAdminContactMessage(
  messageId: string | undefined,
) {
  return useQuery({
    queryKey:
      contactKeys.messageDetail(
        messageId ?? "",
      ),

    queryFn: () =>
      getAdminContactMessage(
        messageId!,
      ),

    enabled:
      Boolean(messageId),
  });
}

export function useUpdateContactMessageStatus() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      messageId,
      status,
    }: {
      messageId: string;
      status: ContactMessageStatus;
    }) =>
      updateContactMessageStatus(
        messageId,
        status,
      ),

    onSuccess: (
      updatedMessage,
    ) => {
      queryClient.setQueryData(
        contactKeys.messageDetail(
          updatedMessage.id,
        ),
        updatedMessage,
      );

      queryClient.invalidateQueries({
        queryKey:
          contactKeys.messages(),
      });
    },
  });
}

export function useDeleteContactMessage() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      messageId: string,
    ) =>
      deleteContactMessage(
        messageId,
      ),

    onSuccess: (
      _,
      messageId,
    ) => {
      queryClient.removeQueries({
        queryKey:
          contactKeys.messageDetail(
            messageId,
          ),
      });

      queryClient.invalidateQueries({
        queryKey:
          contactKeys.messages(),
      });
    },
  });
}