import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import { useAuthStore } from "../../stores/authStore";

import type { UserRole } from "../../features/auth/auth.types";

interface RoleRouteProps {
  roles: UserRole[];
}

export function RoleRoute({
  roles,
}: RoleRouteProps) {
  const location = useLocation();

  const accessToken = useAuthStore(
    (state) => state.accessToken,
  );

  const user = useAuthStore(
    (state) => state.user,
  );

  if (!accessToken || !user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{
          from: location.pathname,
        }}
      />
    );
  }

  if (!roles.includes(user.role)) {
    return (
      <Navigate
        to="/"
        replace
      />
    );
  }

  return <Outlet />;
}