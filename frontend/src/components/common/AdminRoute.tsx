import type { ReactNode } from "react";

import { Navigate, Outlet } from "react-router-dom";

import {
  useCurrentUser,
} from "../../features/auth/auth.hooks";

import {
  useAuthStore,
} from "../../stores/authStore";

interface AdminRouteProps {
  children?: ReactNode;
}

export function AdminRoute({
  children,
}: AdminRouteProps) {
  const user = useAuthStore(
    (state) => state.user,
  );

  const accessToken = useAuthStore(
    (state) => state.accessToken,
  );

  const {
    isLoading,
    isError,
  } = useCurrentUser(
    Boolean(accessToken),
  );

  if (isLoading) {
    return null;
  }

  if (!accessToken || !user || isError) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }

  if (user.role !== "admin") {
    return (
      <Navigate
        to="/admin"
        replace
      />
    );
  }

  return children
    ? children
    : <Outlet />;
}