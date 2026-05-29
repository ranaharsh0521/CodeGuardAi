import { apiClient } from './api-client';
import { Scan } from './scan-service';

export interface UploadScanData {
  files: File[];
  projectName?: string;
}

export interface SupportedExtensions {
  extensions: string[];
  max_file_size_mb: number;
  max_files: number;
}

export const uploadService = {
  async uploadAndScan(data: UploadScanData): Promise<Scan> {
    const formData = new FormData();
    
    // Add files
    data.files.forEach(file => {
      formData.append('files', file);
    });
    
    // Add project name if provided
    if (data.projectName) {
      formData.append('project_name', data.projectName);
    }
    
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/upload/upload-scan`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${apiClient.getToken()}`,
      },
      body: formData,
      credentials: 'include',
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP Error: ${response.status}`);
    }
    
    return response.json();
  },

  async getSupportedExtensions(): Promise<SupportedExtensions> {
    return apiClient.get('/upload/supported-extensions');
  },
};