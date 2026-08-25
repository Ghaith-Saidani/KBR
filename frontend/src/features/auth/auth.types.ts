export type UserRole = 'member' | 'staff' | 'admin'

export type UserStatus =
  | 'pending'
  | 'active'
  | 'suspended'
  | 'archived'

export interface AuthUser {
  id: string
  email: string
  first_name: string
  last_name: string
  role: UserRole
  status: UserStatus
  is_email_verified: boolean
}

export interface RegisterRequest {
  email: string
  password: string
  first_name: string
  last_name: string
}

export interface LoginRequest {
  email: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}