import {
  keepPreviousData,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

import {
  createNews,
  deleteNews,
  getManageNews,
  getNews,
  getNewsById,
  getNewsBySlug,
  updateNews,
} from "./news.api";

import type {
  NewsCreateRequest,
  NewsListParams,
  NewsUpdateRequest,
} from "./news.types";


export const newsKeys = {
  all: ["news"] as const,

  lists: () =>
    [
      ...newsKeys.all,
      "list",
    ] as const,

  list: (
    params: NewsListParams,
  ) =>
    [
      ...newsKeys.lists(),
      params,
    ] as const,

  managementLists: () =>
    [
      ...newsKeys.all,
      "management-list",
    ] as const,

  managementList: (
    params: NewsListParams,
  ) =>
    [
      ...newsKeys.managementLists(),
      params,
    ] as const,

  details: () =>
    [
      ...newsKeys.all,
      "detail",
    ] as const,

  detail: (
    newsId: string,
  ) =>
    [
      ...newsKeys.details(),
      newsId,
    ] as const,

  slugs: () =>
    [
      ...newsKeys.all,
      "slug",
    ] as const,

  slug: (
    slug: string,
  ) =>
    [
      ...newsKeys.slugs(),
      slug,
    ] as const,
};


export function useNews(
  params: NewsListParams = {},
) {
  return useQuery({
    queryKey: newsKeys.list(params),

    queryFn: () =>
      getNews(params),

    placeholderData:
      keepPreviousData,
  });
}


export function useManageNews(
  params: NewsListParams = {},
) {
  return useQuery({
    queryKey:
      newsKeys.managementList(
        params,
      ),

    queryFn: () =>
      getManageNews(params),

    placeholderData:
      keepPreviousData,
  });
}


export function useNewsById(
  newsId: string | undefined,
) {
  return useQuery({
    queryKey:
      newsKeys.detail(
        newsId ?? "",
      ),

    queryFn: () =>
      getNewsById(newsId!),

    enabled:
      Boolean(newsId),
  });
}


export function useNewsBySlug(
  slug: string | undefined,
) {
  return useQuery({
    queryKey:
      newsKeys.slug(
        slug ?? "",
      ),

    queryFn: () =>
      getNewsBySlug(slug!),

    enabled:
      Boolean(slug),
  });
}


export function useCreateNews() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      data: NewsCreateRequest,
    ) =>
      createNews(data),

    onSuccess: (
      createdNews,
    ) => {
      queryClient.setQueryData(
        newsKeys.detail(
          createdNews.id,
        ),
        createdNews,
      );

      queryClient.setQueryData(
        newsKeys.slug(
          createdNews.slug,
        ),
        createdNews,
      );

      queryClient.invalidateQueries({
        queryKey:
          newsKeys.all,
      });
    },
  });
}


export function useUpdateNews() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: ({
      newsId,
      data,
    }: {
      newsId: string;
      data: NewsUpdateRequest;
    }) =>
      updateNews(
        newsId,
        data,
      ),

    onSuccess: (
      updatedNews,
    ) => {
      queryClient.setQueryData(
        newsKeys.detail(
          updatedNews.id,
        ),
        updatedNews,
      );

      queryClient.setQueryData(
        newsKeys.slug(
          updatedNews.slug,
        ),
        updatedNews,
      );

      queryClient.invalidateQueries({
        queryKey:
          newsKeys.all,
      });
    },
  });
}


export function useDeleteNews() {
  const queryClient =
    useQueryClient();

  return useMutation({
    mutationFn: (
      newsId: string,
    ) =>
      deleteNews(newsId),

    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey:
          newsKeys.all,
      });
    },
  });
}