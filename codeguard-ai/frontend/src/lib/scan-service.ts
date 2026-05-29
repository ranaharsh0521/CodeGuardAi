import { apiClient } from './api-client';

export interface Finding {
  tool: string;
  rule_id: string;
  message: string;
  file_path: string;
  line_number: number;
  severity: string;
  code_snippet?: string;
  ai_fix_suggestion?: string;
  ai_explanation?: string;
}

export interface Scan {
  id: number;
  project_id: number;
  project_name?: string;
  status: string;
  progress?: number;
  message?: string;
  error_message?: string;
  risk_score: number;
  findings_count?: number;
  commit_hash?: string;
  findings?: Finding[];
  created_at: string;
  completed_at?: string;
}

export interface ScanResults {
  id: number;
  project_id: number;
  status: string;
  progress: number;
  message?: string;
  error_message?: string;
  risk_score: number;
  findings: Finding[];
  created_at: string;
  completed_at?: string;
}

export interface ScanStatus {
  scan_id: number;
  status: string;
  progress: number;
  message?: string;
  error_message?: string;
  risk_score: number;
  findings_count: number;
  created_at: string;
  completed_at?: string;
}

export interface TriggerScanData {
  project_id: number;
  commit_hash?: string;
}

export const scanService = {
  async triggerScan(data: TriggerScanData): Promise<Scan> {
    return apiClient.post('/scans/', data);
  },

  async getScans(projectId?: number): Promise<Scan[]> {
    const path = projectId ? `/scans/?project_id=${projectId}` : '/scans/';
    return apiClient.get(path);
  },

  async getScanResult(scanId: number): Promise<ScanResults> {
    return apiClient.get(`/scans/${scanId}`);
  },

  async getScanStatus(scanId: number): Promise<ScanStatus> {
    return apiClient.get(`/scans/${scanId}/status`);
  },

  async deleteScan(scanId: number): Promise<void> {
    await apiClient.delete(`/scans/${scanId}`);
  },
};
