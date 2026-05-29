import { apiClient } from './api-client';

const API_ROOT = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1').replace(/\/api\/v1\/?$/, '');

export interface User {
  id: number;
  email: string;
  full_name: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  github_username?: string;
  google_id?: string;
  avatar_url?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface SignupData {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

interface HealthResponse {
  features?: {
    github_oauth?: boolean;
    google_oauth?: boolean;
  };
}

export interface OAuthFeatures {
  github: boolean;
  google: boolean;
}

export const authService = {
  async login(credentials: LoginCredentials): Promise<AuthToken> {
    return apiClient.post('/auth/login', credentials);
  },

  async signup(data: SignupData): Promise<User> {
    return apiClient.post('/auth/register', data);
  },

  async logout(): Promise<void> {
    apiClient.clearToken();
    try {
      await apiClient.post('/auth/logout', {});
    } catch {
      // Local token removal is the source of truth for this stateless JWT logout.
    }
  },

  async getCurrentUser(): Promise<User> {
    return apiClient.get('/users/me');
  },

  isAuthenticated(): boolean {
    return !!apiClient.getToken();
  },

  async getOAuthFeatures(): Promise<OAuthFeatures> {
    try {
      const response = await fetch(`${API_ROOT}/health`);
      if (!response.ok) {
        return { github: false, google: false };
      }
      const health = await response.json() as HealthResponse;
      return {
        github: Boolean(health.features?.github_oauth),
        google: Boolean(health.features?.google_oauth),
      };
    } catch {
      return { github: false, google: false };
    }
  },

  async isGithubAuthEnabled(): Promise<boolean> {
    return (await this.getOAuthFeatures()).github;
  },

  async isGoogleAuthEnabled(): Promise<boolean> {
    return (await this.getOAuthFeatures()).google;
  },

  async getGithubLoginUrl(): Promise<string> {
    const res = await apiClient.get<{ authorization_url: string }>('/auth/github/login');
    return res.authorization_url;
  },

  async loginWithGithub(): Promise<void> {
    if (!(await this.isGithubAuthEnabled())) {
      throw new Error('GitHub login is not configured yet. Add GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in backend/.env, then restart the backend.');
    }
    const url = await this.getGithubLoginUrl();
    window.location.href = url;
  },

  async getGoogleLoginUrl(): Promise<string> {
    const res = await apiClient.get<{ authorization_url: string }>('/auth/google/login');
    return res.authorization_url;
  },

  async loginWithGoogle(): Promise<void> {
    if (!(await this.isGoogleAuthEnabled())) {
      throw new Error('Google login is not configured yet. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in backend/.env, then restart the backend.');
    }
    const url = await this.getGoogleLoginUrl();
    window.location.href = url;
  },
};
