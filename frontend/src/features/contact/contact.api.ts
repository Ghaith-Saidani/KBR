import api from "../../services/api";

import type {
  ContactMessage,
  ContactMessageCreateRequest,
  ContactMessageListParams,
  ContactMessageListResponse,
  ContactMessageStatus,
} from "./contact.types";

export async function submitContactMessage(
  data: ContactMessageCreateRequest,
): Promise<ContactMessage> {
  const response =
    await api.post<ContactMessage>(
      "/contact",
      data,
    );

  return response.data;
}

export async function getAdminContactMessages(
  params: ContactMessageListParams = {},
): Promise<ContactMessageListResponse> {
  const response =
    await api.get<ContactMessageListResponse>(
      "/contact",
      {
        params,
      },
    );

  return response.data;
}

export async function getAdminContactMessage(
  messageId: string,
): Promise<ContactMessage> {
  const response =
    await api.get<ContactMessage>(
      `/contact/${encodeURIComponent(messageId)}`,
    );

  return response.data;
}

export async function updateContactMessageStatus(
  messageId: string,
  status: ContactMessageStatus,
): Promise<ContactMessage> {
  const response =
    await api.patch<ContactMessage>(
      `/contact/${encodeURIComponent(messageId)}`,
      {
        status,
      },
    );

  return response.data;
}

export async function deleteContactMessage(
  messageId: string,
): Promise<void> {
  await api.delete(
    `/contact/${encodeURIComponent(messageId)}`,
  );
}