import { apiClient } from './api-client';

export interface Project {
  id: number;
  name: string;
  description?: string;
  repository_url?: string;
  owner_id?: number;
  team_id?: number;
  created_at: string;
  updated_at?: string;
}

export interface GitHubRepository {
  id: number;
  full_name: string;
  name: string;
  html_url: string;
  clone_url: string;
  private: boolean;
  default_branch?: string;
  description?: string;
  updated_at?: string;
}

export interface CreateProjectData {
  name: string;
  description?: string;
  repository_url?: string;
  team_id?: number;
}

export interface UpdateProjectData {
  name?: string;
  description?: string;
  repository_url?: string;
  team_id?: number;
}

export const projectService = {
  async getAll(): Promise<Project[]> {
    return apiClient.get('/projects/');
  },

  async getGitHubRepositories(): Promise<GitHubRepository[]> {
    return apiClient.get('/projects/github/repositories');
  },

  async getById(projectId: number): Promise<Project> {
    return apiClient.get(`/projects/${projectId}`);
  },

  async create(data: CreateProjectData): Promise<Project> {
    return apiClient.post('/projects/', data);
  },

  async update(projectId: number, data: UpdateProjectData): Promise<Project> {
    return apiClient.put(`/projects/${projectId}`, data);
  },

  async delete(projectId: number): Promise<void> {
    await apiClient.delete(`/projects/${projectId}`);
  },
};
