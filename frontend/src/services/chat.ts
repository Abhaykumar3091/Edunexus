import { ApiClient } from './api';
import { ChatMessage, ChatResponse } from '@/types/student';
import { ApiResponse } from '@/types/api';

export const chatService = {
  sendMessage(
    message: string,
    history: ChatMessage[] = []
  ): Promise<ApiResponse<ChatResponse>> {
    return ApiClient.post<ChatResponse>('/chat/message', { message, history });
  },
};
