import {
  beforeEach,
  describe,
  expect,
  it,
} from "vitest";

import {
  useAuthStore,
} from "./authStore";

describe(
  "authStore",
  () => {
    beforeEach(() => {
      useAuthStore
        .getState()
        .clearAuthentication();

      localStorage.clear();
    });

    it(
      "starts unauthenticated",
      () => {
        const state =
          useAuthStore.getState();

        expect(
          state.accessToken,
        ).toBeNull();

        expect(
          state.user,
        ).toBeNull();

        expect(
          state.isAuthenticated(),
        ).toBe(false);
      },
    );

    it(
      "stores authentication data",
      () => {
        const user = {
          id: "user-1",
          email: "member@kbr.tn",
          role: "member" as const,
          status: "active" as const,
          is_email_verified: true,
          created_at:
            "2026-08-01T00:00:00Z",
        };

        useAuthStore
          .getState()
          .setAuthentication(
            "test-access-token",
            user,
          );

        const state =
          useAuthStore.getState();

        expect(
          state.accessToken,
        ).toBe(
          "test-access-token",
        );

        expect(
          state.user,
        ).toEqual(user);

        expect(
          state.isAuthenticated(),
        ).toBe(true);
      },
    );

    it(
      "updates the current user",
      () => {
        const user = {
          id: "user-1",
          email: "member@kbr.tn",
          role: "member" as const,
          status: "active" as const,
          is_email_verified: true,
          created_at:
            "2026-08-01T00:00:00Z",
        };

        useAuthStore
          .getState()
          .setUser(user);

        expect(
          useAuthStore
            .getState()
            .user,
        ).toEqual(user);
      },
    );

    it(
      "clears authentication",
      () => {
        const user = {
          id: "user-1",
          email: "member@kbr.tn",
          role: "member" as const,
          status: "active" as const,
          is_email_verified: true,
          created_at:
            "2026-08-01T00:00:00Z",
        };

        useAuthStore
          .getState()
          .setAuthentication(
            "token",
            user,
          );

        useAuthStore
          .getState()
          .clearAuthentication();

        const state =
          useAuthStore.getState();

        expect(
          state.accessToken,
        ).toBeNull();

        expect(
          state.user,
        ).toBeNull();

        expect(
          state.isAuthenticated(),
        ).toBe(false);
      },
    );
  },
);