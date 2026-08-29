import {
  describe,
  expect,
  it,
  beforeEach,
} from "vitest";

import {
  render,
  screen,
} from "@testing-library/react";

import {
  MemoryRouter,
  Routes,
  Route,
} from "react-router-dom";

import { ProtectedRoute } from "./ProtectedRoute";
import { useAuthStore } from "../../stores/authStore";

function ProtectedPage() {
  return (
    <div>
      Protected content
    </div>
  );
}

function LoginPage() {
  return (
    <div>
      Login page
    </div>
  );
}

describe("ProtectedRoute", () => {
  beforeEach(() => {
    useAuthStore.getState().clearAuthentication();
  });

  it("redirects unauthenticated users to login", () => {
    render(
      <MemoryRouter initialEntries={["/account"]}>
        <Routes>
          <Route
            path="/login"
            element={<LoginPage />}
          />

          <Route element={<ProtectedRoute />}>
            <Route
              path="/account"
              element={<ProtectedPage />}
            />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText("Login page"),
    ).toBeInTheDocument();

    expect(
      screen.queryByText("Protected content"),
    ).not.toBeInTheDocument();
  });

  it("allows authenticated users to access protected pages", () => {
    useAuthStore
      .getState()
      .setAuthentication(
        "test-access-token",
        {
          id: "test-user-id",
          email: "member@kbr.tn",
          role: "member",
          status: "active",
          is_email_verified: true,
          created_at:
            "2026-01-01T00:00:00Z",
        },
      );

    render(
      <MemoryRouter initialEntries={["/account"]}>
        <Routes>
          <Route element={<ProtectedRoute />}>
            <Route
              path="/account"
              element={<ProtectedPage />}
            />
          </Route>

          <Route
            path="/login"
            element={<LoginPage />}
          />
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText("Protected content"),
    ).toBeInTheDocument();

    expect(
      screen.queryByText("Login page"),
    ).not.toBeInTheDocument();
  });
});