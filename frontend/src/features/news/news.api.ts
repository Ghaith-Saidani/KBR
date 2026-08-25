import api from "../../services/api";

import type {
  News,
  NewsCreateRequest,
  NewsListParams,
  NewsListResponse,
  NewsUpdateRequest,
} from "./news.types";


export async function getNews(
  params: NewsListParams = {},
): Promise<NewsListResponse> {
  const response = await api.get<NewsListResponse>(
    "/news",
    {
      params,
    },
  );

  return response.data;
}


export async function getManageNews(
  params: NewsListParams = {},
): Promise<NewsListResponse> {
  const response = await api.get<NewsListResponse>(
    "/news/manage",
    {
      params,
    },
  );

  return response.data;
}


export async function getNewsById(
  newsId: string,
): Promise<News> {
  const response = await api.get<News>(
    `/news/${encodeURIComponent(newsId)}`,
  );

  return response.data;
}


export async function getNewsBySlug(
  slug: string,
): Promise<News> {
  const response = await api.get<News>(
    `/news/slug/${encodeURIComponent(slug)}`,
  );

  return response.data;
}


export async function createNews(
  data: NewsCreateRequest,
): Promise<News> {
  const response = await api.post<News>(
    "/news",
    data,
  );

  return response.data;
}


export async function updateNews(
  newsId: string,
  data: NewsUpdateRequest,
): Promise<News> {
  const response = await api.patch<News>(
    `/news/${encodeURIComponent(newsId)}`,
    data,
  );

  return response.data;
}


export async function deleteNews(
  newsId: string,
): Promise<void> {
  await api.delete(
    `/news/${encodeURIComponent(newsId)}`,
  );
}