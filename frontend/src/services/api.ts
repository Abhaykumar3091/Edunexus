import { ApiResponse } from '@/types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export class ApiClient {
  private static getToken(): string | null {
    return localStorage.getItem('uniassist_token');
  }

  static async request<T = any>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...((options.headers as Record<string, string>) || {}),
    };

    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }

    const url = endpoint.startsWith('http') ? endpoint : API_BASE_URL + endpoint;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data: ApiResponse<T> = await response.json();

      if (!response.ok) {
        return {
          success: false,
          error: data.error || {
            code: 'HTTP_' + response.status,
            message: data.message || ('Request failed with status ' + response.status),
          },
        };
      }

      return data;
    } catch (err: any) {
      return {
        success: false,
        error: {
          code: 'NETWORK_ERROR',
          message: err.message || 'Network communication failure. Please verify backend is running.',
        },
      };
    }
  }

  static get<T = any>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'GET' });
  }

  static post<T = any>(endpoint: string, body?: any) {
    return this.request<T>(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  static put<T = any>(endpoint: string, body?: any) {
    return this.request<T>(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined,
    });
  }

  static delete<T = any>(endpoint: string) {
    return this.request<T>(endpoint, { method: 'DELETE' });
  }

  /** Multipart file upload - lets the browser set correct Content-Type with boundary. */
  static async uploadFile<T = any>(endpoint: string, formData: FormData): Promise<ApiResponse<T>> {
    const token = this.getToken();
    const headers: Record<string, string> = { Accept: 'application/json' };
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    const url = endpoint.startsWith('http') ? endpoint : API_BASE_URL + endpoint;
    try {
      const response = await fetch(url, { method: 'POST', headers, body: formData });
      const data: ApiResponse<T> = await response.json();
      if (!response.ok) {
        return {
          success: false,
          error: data.error || {
            code: 'HTTP_' + response.status,
            message: data.message || ('Upload failed with status ' + response.status),
          },
        };
      }
      return data;
    } catch (err: any) {
      return {
        success: false,
        error: { code: 'NETWORK_ERROR', message: err.message || 'Network communication failure.' },
      };
    }
  }
}
