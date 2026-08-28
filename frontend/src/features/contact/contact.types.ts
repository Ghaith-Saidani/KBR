export type ContactMessageStatus =
  | "new"
  | "read"
  | "replied"
  | "archived";

export interface ContactMessageCreateRequest {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export interface ContactMessage {
  id: string;
  name: string;
  email: string;
  subject: string;
  message: string;
  status: ContactMessageStatus;
  user_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ContactMessageListParams {
  skip?: number;
  limit?: number;
  search?: string;
  status?: ContactMessageStatus;
}

export interface ContactMessageListResponse {
  items: ContactMessage[];
  total: number;
  skip: number;
  limit: number;
}