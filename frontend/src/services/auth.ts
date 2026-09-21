import { ApiClient } from './api';
import { AuthToken, User } from '@/types/user';
import { ApiResponse, HealthStatus } from '@/types/api';

export const authService = {
  async login(email: string, password: string): Promise<ApiResponse<AuthToken>> {
    const res = await ApiClient.post<AuthToken>('/auth/login', { email, password });
    if (res.success && res.data?.access_token) {
      localStorage.setItem('uniassist_token', res.data.access_token);
      localStorage.setItem('uniassist_user', JSON.stringify(res.data));
    }
    return res;
  },

  async register(data: {
    email: string;
    password: string;
    full_name: string;
    role?: string;
    university_id?: string;
  }): Promise<ApiResponse<User>> {
    return ApiClient.post<User>('/auth/register', data);
  },

  async getMe(): Promise<ApiResponse<User>> {
    return ApiClient.get<User>('/auth/me');
  },

  async checkHealth(): Promise<ApiResponse<HealthStatus>> {
    return ApiClient.get<HealthStatus>('/health');
  },

  logout(): void {
    localStorage.removeItem('uniassist_token');
    localStorage.removeItem('uniassist_user');
  },

  getStoredToken(): string | null {
    return localStorage.getItem('uniassist_token');
  },
};
