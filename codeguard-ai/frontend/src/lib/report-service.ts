import { apiClient } from './api-client';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const reportService = {
  async downloadPdf(scanId: number): Promise<void> {
    const token = apiClient.getToken();
    const response = await fetch(`${API_BASE_URL}/reports/${scanId}/pdf`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to download PDF (${response.status})`);
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `codeguard_scan_${scanId}_report.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  },

  async downloadJson(scanId: number): Promise<void> {
    const data = await apiClient.get<Record<string, unknown>>(`/reports/${scanId}/json`);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `codeguard_scan_${scanId}_report.json`;
    a.click();
    URL.revokeObjectURL(url);
  },
};
