import {
  useMutation,
} from "@tanstack/react-query";

import { sendAIChat } from "./ai.api";
import type {
  AIChatRequest,
} from "./ai.types";

export function useAIChat() {
  return useMutation({
    mutationFn: (
      request: AIChatRequest,
    ) => sendAIChat(request),

    retry: 0,
  });
}