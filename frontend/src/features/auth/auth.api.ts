import api from '../../services/api'

import type {
  AuthUser,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
} from './auth.types'

export async function registerUser(
  data: RegisterRequest,
): Promise<AuthUser> {
  const response = await api.post<AuthUser>(
    '/auth/register',
    data,
  )

  return response.data
}

export async function loginUser(
  data: LoginRequest,
): Promise<TokenResponse> {
  const response = await api.post<TokenResponse>(
    '/auth/login',
    data,
  )

  return response.data
}

export async function getCurrentUser(): Promise<AuthUser> {
  const response = await api.get<AuthUser>(
    '/auth/me',
  )

  return response.data
}