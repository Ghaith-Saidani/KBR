import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createEvent,
  deleteEvent,
  getEvent,
  getEvents,
  getManageEvents,
  updateEvent,
} from "./events.api";

import type {
  EventCreateRequest,
  EventListParams,
  EventUpdateRequest,
} from "./events.types";

export const eventKeys = {
  all: ["events"] as const,

  lists: () =>
    [...eventKeys.all, "list"] as const,

  list: (params: EventListParams) =>
    [...eventKeys.lists(), params] as const,

  managementLists: () =>
    [...eventKeys.all, "management-list"] as const,

  managementList: (params: EventListParams) =>
    [
      ...eventKeys.managementLists(),
      params,
    ] as const,

  details: () =>
    [...eventKeys.all, "detail"] as const,

  detail: (eventId: string) =>
    [
      ...eventKeys.details(),
      eventId,
    ] as const,
};

export function useEvents(
  params: EventListParams = {},
) {
  return useQuery({
    queryKey: eventKeys.list(params),

    queryFn: () =>
      getEvents(params),

    placeholderData:
      keepPreviousData,
  });
}

export function useManageEvents(
  params: EventListParams = {},
) {
  return useQuery({
    queryKey:
      eventKeys.managementList(params),

    queryFn: () =>
      getManageEvents(params),

    placeholderData:
      keepPreviousData,
  });
}

export function useEvent(
  eventId: string | undefined,
) {
  return useQuery({
    queryKey: eventKeys.detail(
      eventId ?? "",
    ),

    queryFn: () =>
      getEvent(eventId!),

    enabled:
      Boolean(eventId),
  });
}

export function useCreateEvent() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      data: EventCreateRequest,
    ) => createEvent(data),

    onSuccess: (createdEvent) => {
      queryClient.setQueryData(
        eventKeys.detail(
          createdEvent.id,
        ),
        createdEvent,
      );

      queryClient.invalidateQueries({
        queryKey: eventKeys.all,
      });
    },
  });
}

export function useUpdateEvent() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      eventId,
      data,
    }: {
      eventId: string;
      data: EventUpdateRequest;
    }) =>
      updateEvent(
        eventId,
        data,
      ),

    onSuccess: (
      updatedEvent,
    ) => {
      queryClient.setQueryData(
        eventKeys.detail(
          updatedEvent.id,
        ),
        updatedEvent,
      );

      queryClient.invalidateQueries({
        queryKey: eventKeys.all,
      });
    },
  });
}

export function useDeleteEvent() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      eventId: string,
    ) => deleteEvent(eventId),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: eventKeys.all,
      });
    },
  });
}