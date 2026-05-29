import { apiClient } from './api-client';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
}

export interface ChatRequest {
  message: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  reply: string;
}

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return apiClient.post('/chat/', request);
  },
};
