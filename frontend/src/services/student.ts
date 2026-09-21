import { ApiClient } from './api';
import { User } from '@/types/user';
import {
  StudentProfile,
  Complaint,
  CreateComplaintInput,
  ChatMessage,
  ChatResponse,
  AdminStats,
  DocumentItem,
  ComplaintStatus,
} from '@/types/student';

export const studentService = {
  getProfile: () =>
    ApiClient.get<StudentProfile>('/student/profile'),

  getComplaints: () =>
    ApiClient.get<Complaint[]>('/student/complaints'),

  createComplaint: (data: CreateComplaintInput) =>
    ApiClient.post<Complaint>('/student/complaints', data),

  sendChatMessage: (message: string, conversationId?: string, history: ChatMessage[] = []) =>
    ApiClient.post<ChatResponse>('/chat/message', {
      message,
      conversation_id: conversationId,
      history,
    }),

  getAdminStats: () =>
    ApiClient.get<AdminStats>('/admin/stats'),

  getAdminUsers: () =>
    ApiClient.get<User[]>('/admin/users'),

  getAdminComplaints: () =>
    ApiClient.get<Complaint[]>('/admin/complaints'),

  getAdminDocuments: () =>
    ApiClient.get<DocumentItem[]>('/admin/documents'),

  updateComplaintStatus: (ticketId: string | number, status: ComplaintStatus, notes?: string) =>
    ApiClient.put<Complaint>(`/admin/complaints/${ticketId}/status`, {
      status,
      resolution_notes: notes,
    }),
};
