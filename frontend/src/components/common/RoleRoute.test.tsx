import {
  beforeEach,
  describe,
  expect,
  it,
} from "vitest";

import {
  render,
  screen,
} from "@testing-library/react";

import {
  MemoryRouter,
  Route,
  Routes,
} from "react-router-dom";

import { RoleRoute } from "./RoleRoute";

import {
  useAuthStore,
} from "../../stores/authStore";

function AdminPage() {
  return (
    <div>
      Admin content
    </div>
  );
}

function HomePage() {
  return (
    <div>
      Home content
    </div>
  );
}

function LoginPage() {
  return (
    <div>
      Login content
    </div>
  );
}

const memberUser = {
  id: "member-id",
  email: "member@kbr.tn",
  role: "member" as const,
  status: "active" as const,
  is_email_verified: true,
  created_at:
    "2026-01-01T00:00:00Z",
};

const staffUser = {
  id: "staff-id",
  email: "staff@kbr.tn",
  role: "staff" as const,
  status: "active" as const,
  is_email_verified: true,
  created_at:
    "2026-01-01T00:00:00Z",
};

describe("RoleRoute", () => {
  beforeEach(() => {
    useAuthStore
      .getState()
      .clearAuthentication();
  });

  it("redirects unauthenticated users to login", () => {
    render(
      <MemoryRouter
        initialEntries={["/admin"]}
      >
        <Routes>
          <Route
            path="/login"
            element={<LoginPage />}
          />

          <Route
            element={
              <RoleRoute
                roles={[
                  "staff",
                  "admin",
                ]}
              />
            }
          >
            <Route
              path="/admin"
              element={<AdminPage />}
            />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText(
        "Login content",
      ),
    ).toBeInTheDocument();
  });

  it("redirects members away from admin routes", () => {
    useAuthStore
      .getState()
      .setAuthentication(
        "member-token",
        memberUser,
      );

    render(
      <MemoryRouter
        initialEntries={["/admin"]}
      >
        <Routes>
          <Route
            path="/"
            element={<HomePage />}
          />

          <Route
            element={
              <RoleRoute
                roles={[
                  "staff",
                  "admin",
                ]}
              />
            }
          >
            <Route
              path="/admin"
              element={<AdminPage />}
            />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText(
        "Home content",
      ),
    ).toBeInTheDocument();

    expect(
      screen.queryByText(
        "Admin content",
      ),
    ).not.toBeInTheDocument();
  });

  it("allows staff users to access admin routes", () => {
    useAuthStore
      .getState()
      .setAuthentication(
        "staff-token",
        staffUser,
      );

    render(
      <MemoryRouter
        initialEntries={["/admin"]}
      >
        <Routes>
          <Route
            path="/"
            element={<HomePage />}
          />

          <Route
            element={
              <RoleRoute
                roles={[
                  "staff",
                  "admin",
                ]}
              />
            }
          >
            <Route
              path="/admin"
              element={<AdminPage />}
            />
          </Route>
        </Routes>
      </MemoryRouter>,
    );

    expect(
      screen.getByText(
        "Admin content",
      ),
    ).toBeInTheDocument();
  });
});