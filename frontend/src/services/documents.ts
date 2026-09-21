import { ApiClient } from './api';
import { ApiResponse } from '@/types/api';

export interface DocumentSection {
  page_number: number;
  title: string;
  content: string;
}

export interface AnalyzedDocument {
  document_id: string;
  filename: string;
  file_type: string;
  page_count: number;
  word_count: number;
  summary_preview: string;
  sections: DocumentSection[];
}

export interface DocumentCitation {
  source_file: string;
  snippet: string;
  document_id: string;
}

export interface DocumentQAResponse {
  answer: string;
  citations: DocumentCitation[];
  found: boolean;
}

export interface RagUploadResult {
  success: boolean;
  blob_name: string;
  container: string;
  url: string;
  size_bytes: number;
  content_type: string;
  rag_container: string;
  rag_ready: boolean;
  metadata: Record<string, any>;
}

export const documentService = {
  async uploadAndAnalyze(file: File): Promise<ApiResponse<AnalyzedDocument>> {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('uniassist_token');
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }

    try {
      const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
      const res = await fetch('http://localhost:8000' + API_BASE_URL + '/documents/analyze', {
        method: 'POST',
        headers,
        body: formData,
      });

      const json = await res.json();
      if (!res.ok) {
        return {
          success: false,
          error: { code: 'UPLOAD_FAILED', message: json.detail || 'Failed to analyze document.' },
        };
      }
      return { success: true, data: json };
    } catch (err: any) {
      return {
        success: false,
        error: { code: 'NETWORK_ERROR', message: err.message || 'Error connecting to server.' },
      };
    }
  },

  async uploadForRag(file: File, category: string = 'policy'): Promise<ApiResponse<RagUploadResult>> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    return ApiClient.uploadFile<RagUploadResult>('/documents/upload-rag', formData);
  },

  async listRagDocuments(): Promise<ApiResponse<any[]>> {
    return ApiClient.get<any[]>('/documents/rag-list');
  },

  async askQuestion(
    document_id: string,
    question: string,
    history: { role: string; content: string }[] = []
  ): Promise<ApiResponse<DocumentQAResponse>> {
    return ApiClient.post<DocumentQAResponse>('/documents/ask', {
      document_id,
      question,
      history,
    });
  },
};
