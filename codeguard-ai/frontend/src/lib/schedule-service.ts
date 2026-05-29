import { apiClient } from './api-client';

export interface ScheduledScan {
  id: number;
  project_id: number;
  interval_hours: number;
  enabled: boolean;
  notify_email: boolean;
  last_run_at?: string;
  next_run_at?: string;
  created_at: string;
}

export const scheduleService = {
  async list(): Promise<ScheduledScan[]> {
    return apiClient.get('/schedules/');
  },

  async create(projectId: number, intervalHours: number, notifyEmail = true): Promise<ScheduledScan> {
    return apiClient.post('/schedules/', {
      project_id: projectId,
      interval_hours: intervalHours,
      notify_email: notifyEmail,
    });
  },

  async toggle(scheduleId: number): Promise<ScheduledScan> {
    return apiClient.post(`/schedules/${scheduleId}/toggle`, {});
  },

  async delete(scheduleId: number): Promise<void> {
    await apiClient.delete(`/schedules/${scheduleId}`);
  },
};
