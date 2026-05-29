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
  workflow_status?: FindingWorkflowStatus;
  workflow_comment?: string;
  workflow_assignee?: string;
  workflow_updated_at?: string;
}

export type FindingWorkflowStatus = 'open' | 'resolved' | 'ignored' | 'false_positive';

export interface FindingWorkflowUpdate {
  status: FindingWorkflowStatus;
  comment?: string;
  assignee?: string;
}

export interface FindingWorkflowResponse {
  scan_id: number;
  finding_index: number;
  finding: Finding;
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
  quality_gate_result?: {
    passed?: boolean;
    summary?: string;
    gates?: Array<{ name: string; threshold: number; actual: number; passed: boolean }>;
  };
  created_at: string;
  completed_at?: string;
}

export interface ScanComparison {
  current_scan_id: number;
  base_scan_id: number | null;
  project_id: number;
  current_risk_score: number;
  base_risk_score: number | null;
  risk_delta: number | null;
  current_findings_count: number;
  base_findings_count: number;
  new_findings_count: number;
  resolved_findings_count: number;
  unchanged_findings_count: number;
  new_findings: Finding[];
  resolved_findings: Finding[];
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

  async compareScan(scanId: number, baseScanId?: number): Promise<ScanComparison> {
    const suffix = baseScanId ? `?base_scan_id=${baseScanId}` : '';
    return apiClient.get(`/scans/${scanId}/comparison${suffix}`);
  },

  async updateFindingWorkflow(
    scanId: number,
    findingIndex: number,
    data: FindingWorkflowUpdate,
  ): Promise<FindingWorkflowResponse> {
    return apiClient.put(`/scans/${scanId}/findings/${findingIndex}/workflow`, data);
  },

  async deleteScan(scanId: number): Promise<void> {
    await apiClient.delete(`/scans/${scanId}`);
  },
};
