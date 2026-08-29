import api from "../../services/api";

import type {
  AIChatRequest,
  AIChatResponse,
} from "./ai.types";

export async function sendAIChat(
  request: AIChatRequest,
): Promise<AIChatResponse> {
  const response = await api.post<AIChatResponse>(
    "/ai/chat",
    request,
  );

  return response.data;
}