export type AIMessageRole =
  | "user"
  | "assistant";

export interface AIMessage {
  id: string;
  role: AIMessageRole;
  content: string;
}

export interface AIRequestMessage {
  role: "user" | "assistant";
  content: string;
}

export interface AIChatRequest {
  messages: AIRequestMessage[];
  temperature?: number;
  max_tokens?: number;
}

export interface AIModelUsage {
  prompt_tokens: number | null;
  completion_tokens: number | null;
  total_tokens: number | null;
}

export interface AIChatResponse {
  content: string;
  model: string;
  provider: string;
  usage?: AIModelUsage | null;
  finish_reason?: string | null;
}