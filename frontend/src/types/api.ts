export interface ApiError {
  code: string;
  message: string;
  details?: any;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: ApiError;
}

export interface HealthStatus {
  app_name: string;
  version: string;
  environment: string;
  status: string;
  database: string;
  timestamp: string;
  services: {
    azure_openai_configured: boolean;
    azure_search_configured: boolean;
    azure_blob_storage_configured: boolean;
    key_vault_configured: boolean;
  };
}
