import {
  useMutation,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'

import { useAuthStore } from '../../stores/authStore'

import {
  getCurrentUser,
  loginUser,
  registerUser,
} from './auth.api'

import type {
  LoginRequest,
  RegisterRequest,
} from './auth.types'

export function useLogin() {
  const setAuthentication =
    useAuthStore((state) => state.setAuthentication)

  return useMutation({
    mutationFn: (data: LoginRequest) =>
      loginUser(data),

    onSuccess: (data) => {
      setAuthentication(
        data.access_token,
        data.user,
      )
    },
  })
}

export function useRegister() {
  return useMutation({
    mutationFn: (data: RegisterRequest) =>
      registerUser(data),
  })
}

export function useCurrentUser(
  enabled = true,
) {
  const accessToken =
    useAuthStore((state) => state.accessToken)

  const setAuthentication =
    useAuthStore((state) => state.setAuthentication)

  return useQuery({
    queryKey: ['auth', 'me'],

    queryFn: async () => {
      const user = await getCurrentUser()

      if (accessToken) {
        setAuthentication(
          accessToken,
          user,
        )
      }

      return user
    },

    enabled:
      enabled &&
      Boolean(accessToken),

    retry: false,
  })
}

export function useLogout() {
  const queryClient =
    useQueryClient()

  const clearAuthentication =
    useAuthStore(
      (state) => state.clearAuthentication,
    )

  return () => {
    clearAuthentication()

    queryClient.removeQueries({
      queryKey: ['auth'],
    })
  }
}