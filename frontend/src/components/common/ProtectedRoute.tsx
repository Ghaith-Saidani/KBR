import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import { useAuthStore } from "../../stores/authStore";

export function ProtectedRoute() {
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

  return <Outlet />;
}