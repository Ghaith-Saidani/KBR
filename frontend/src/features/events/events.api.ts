import api from "../../services/api";

import type {
  Event,
  EventCreateRequest,
  EventListParams,
  EventListResponse,
  EventUpdateRequest,
} from "./events.types";

export async function getEvents(
  params: EventListParams = {},
): Promise<EventListResponse> {
  const response = await api.get<EventListResponse>(
    "/events",
    {
      params,
    },
  );

  return response.data;
}

export async function getManageEvents(
  params: EventListParams = {},
): Promise<EventListResponse> {
  const response = await api.get<EventListResponse>(
    "/events/manage",
    {
      params,
    },
  );

  return response.data;
}

export async function getManageEvent(
  eventId: string,
): Promise<Event> {
  const response = await api.get<Event>(
    `/events/manage/${encodeURIComponent(eventId)}`,
  );

  return response.data;
}

export async function getEvent(
  eventId: string,
): Promise<Event> {
  const response = await api.get<Event>(
    `/events/${encodeURIComponent(eventId)}`,
  );

  return response.data;
}

export async function createEvent(
  data: EventCreateRequest,
): Promise<Event> {
  const response = await api.post<Event>(
    "/events",
    data,
  );

  return response.data;
}

export async function updateEvent(
  eventId: string,
  data: EventUpdateRequest,
): Promise<Event> {
  const response = await api.patch<Event>(
    `/events/${encodeURIComponent(eventId)}`,
    data,
  );

  return response.data;
}

export async function deleteEvent(
  eventId: string,
): Promise<void> {
  await api.delete(
    `/events/${encodeURIComponent(eventId)}`,
  );
}