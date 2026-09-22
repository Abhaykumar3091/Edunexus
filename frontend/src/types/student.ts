export type ComplaintCategory = 'HOSTEL' | 'ACADEMIC' | 'INFRASTRUCTURE' | 'ADMINISTRATIVE' | 'OTHER';
export type ComplaintStatus = 'SUBMITTED' | 'IN_REVIEW' | 'RESOLVED' | 'CLOSED';

export interface StudentProfile {
  id: number;
  user_id: number;
  full_name: string;
  email: string;
  university_id: string;
  program: string;
  semester: number;
  section: string;
  batch_year: number;
  cgpa?: number;
}

export interface Complaint {
  id: number;
  ticket_id: string;
  category: ComplaintCategory;
  title: string;
  description: string;
  status: ComplaintStatus;
  assigned_to?: string;
  resolution_notes?: string;
  created_at: string;
  resolved_at?: string;
}

export interface CreateComplaintInput {
  category: ComplaintCategory;
  title: string;
  description: string;
}

export interface SourceCitation {
  document_title?: string;
  title?: string;
  section?: string;
  chunk_text?: string;
  snippet?: string;
  relevance_score: number;
  url?: string;
}

export type ChatSource = SourceCitation;

export interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: SourceCitation[];
  data_sources?: string[];
  timestamp?: string;
}

export interface ChatResponse {
  message?: string;
  answer?: string;
  sources: SourceCitation[];
  data_sources?: string[];
  conversation_id: string;
}

export interface AdminStats {
  total_students: number;
  total_faculty?: number;
  total_users?: number;
  total_documents?: number;
  total_complaints?: number;
  open_complaints?: number;
  resolved_complaints?: number;
}

export interface UserItem {
  id: number;
  email: string;
  full_name: string;
  role: string;
  university_id: string;
  is_active: boolean;
  created_at?: string;
}

export interface DocumentItem {
  id: number;
  title: string;
  category: string;
  blob_url: string;
  uploaded_at: string;
}
