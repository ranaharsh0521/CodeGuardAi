const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export interface APIError {
  detail: string;
}

export interface APIResponse<T> {
  data?: T;
  error?: APIError;
}

export class APIRequestError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = 'APIRequestError';
    this.status = status;
  }
}

class APIClient {
  private token: string | null = null;

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
  }

  getToken(): string | null {
    if (typeof window !== 'undefined') {
      return this.token || localStorage.getItem('access_token');
    }
    return this.token;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    return headers;
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      let errorMessage = `HTTP Error: ${response.status}`;
      try {
        const errorData = await response.json() as Partial<Record<'detail' | 'message', unknown>>;
        const detail = errorData.detail || errorData.message;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          errorMessage = detail
            .map((item) => {
              if (typeof item === 'string') return item;
              if (item && typeof item === 'object' && 'msg' in item) {
                return String((item as { msg: unknown }).msg);
              }
              return '';
            })
            .filter(Boolean)
            .join(', ') || errorMessage;
        }
      } catch {
        // If response is not JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }

      if (response.status === 401) {
        this.clearToken();
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/signup')) {
          window.location.href = '/login';
        }
      }

      throw new APIRequestError(errorMessage, response.status);
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return response.json();
    }

    // Handle non-JSON responses
    return response.text() as unknown as T;
  }

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'GET',
      headers: this.getHeaders(),
    });
    return this.handleResponse<T>(response);
  }

  async post<T>(path: string, data: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse<T>(response);
  }

  async put<T>(path: string, data: unknown): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    });
    return this.handleResponse<T>(response);
  }

  async delete<T>(path: string): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    });
    return this.handleResponse<T>(response);
  }
}

export const apiClient = new APIClient();
