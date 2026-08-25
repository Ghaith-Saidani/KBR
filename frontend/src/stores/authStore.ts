import { create } from 'zustand'
import { persist } from 'zustand/middleware'

import type { AuthUser } from '../features/auth/auth.types'

interface AuthState {
  accessToken: string | null
  user: AuthUser | null

  setAuthentication: (
    accessToken: string,
    user: AuthUser,
  ) => void

  clearAuthentication: () => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,

      setAuthentication: (accessToken, user) => {
        set({
          accessToken,
          user,
        })
      },

      clearAuthentication: () => {
        set({
          accessToken: null,
          user: null,
        })
      },
    }),
    {
      name: 'kbr-auth',
    },
  ),
)