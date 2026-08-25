import axios from "axios";

import { useAuthStore } from "../stores/authStore";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

if (!API_BASE_URL) {
  console.warn(
    "VITE_API_BASE_URL is not configured. API requests may fail.",
  );
}

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 15_000,
});

api.interceptors.request.use(
  (config) => {
    const accessToken =
      useAuthStore.getState().accessToken;

    if (accessToken) {
      config.headers.Authorization =
        `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      const requestUrl = error.config?.url ?? "";

      const isAuthRequest =
        requestUrl.includes("/auth/login") ||
        requestUrl.includes("/auth/register");

      if (!isAuthRequest) {
        useAuthStore
          .getState()
          .clearAuthentication();

        const currentPath =
          window.location.pathname;

        if (
          currentPath !== "/login" &&
          currentPath !== "/register"
        ) {
          window.location.href = "/login";
        }
      }
    }

    return Promise.reject(error);
  },
);

export default api;