import { apiClient } from './api-client';

export interface Team {
  id: number;
  name: string;
  owner_id: number;
  role: string;
  member_count: number;
  created_at: string;
}

export interface TeamMember {
  user_id: number;
  email: string;
  full_name: string;
  role: string;
  avatar_url?: string;
}

export const teamService = {
  async list(): Promise<Team[]> {
    return apiClient.get('/teams/');
  },

  async create(name: string): Promise<Team> {
    return apiClient.post('/teams/', { name });
  },

  async invite(teamId: number, email: string, role = 'member'): Promise<{ message: string }> {
    return apiClient.post(`/teams/${teamId}/invite`, { email, role });
  },

  async members(teamId: number): Promise<TeamMember[]> {
    return apiClient.get(`/teams/${teamId}/members`);
  },
};
