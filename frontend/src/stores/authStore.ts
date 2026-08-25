import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { AuthUser } from "../features/auth/auth.types";

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;

  setAuthentication: (
    accessToken: string,
    user: AuthUser,
  ) => void;

  setUser: (user: AuthUser) => void;

  clearAuthentication: () => void;

  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      accessToken: null,
      user: null,

      setAuthentication: (
        accessToken,
        user,
      ) => {
        set({
          accessToken,
          user,
        });
      },

      setUser: (user) => {
        set({
          user,
        });
      },

      clearAuthentication: () => {
        set({
          accessToken: null,
          user: null,
        });
      },

      isAuthenticated: () => {
        const {
          accessToken,
          user,
        } = get();

        return Boolean(
          accessToken && user,
        );
      },
    }),
    {
      name: "kbr-auth",
    },
  ),
);