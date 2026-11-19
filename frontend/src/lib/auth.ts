import { apiClient } from './api';
import { User } from '@/types';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  refresh_token?: string;
  token_type: string;
  user?: User;
}

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
  role: 'student' | 'teacher' | 'inst_admin' | 'platform_admin';
  institution_id?: string | null;
}

export async function loginApi(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/login', credentials);
  return response.data;
}

export async function registerApi(data: RegisterData): Promise<User> {
  const response = await apiClient.post<User>('/auth/register', data);
  return response.data;
}

export async function getPublicInstitutionsApi(): Promise<Array<{ id: string; name: string; slug: string; is_demo: boolean }>> {
  const response = await apiClient.get<Array<{ id: string; name: string; slug: string; is_demo: boolean }>>('/institutions/public');
  return response.data;
}

export async function refreshApi(refreshToken?: string | null): Promise<AuthResponse> {
  const response = await apiClient.post<AuthResponse>('/auth/refresh', {
    refresh_token: refreshToken || localStorage.getItem('coglearn_refresh_token'),
  });
  return response.data;
}

export async function logoutApi(): Promise<void> {
  try {
    await apiClient.post('/auth/logout');
  } catch {
    // Ignore backend logout error, clear locally
  }
}

export async function getCurrentUserApi(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
}

export async function forgotPasswordApi(email: string): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>('/auth/forgot-password', { email });
  return response.data;
}

