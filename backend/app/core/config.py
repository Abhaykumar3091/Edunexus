import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Application Information
    APP_NAME: str = "UniAssist AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"

    # Security & Authentication
    SECRET_KEY: str = "uniassist-insecure-dev-secret-key-change-in-production-min32chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database Configuration (Async-first SQLAlchemy 2.0)
    DATABASE_URL: str = (
        "postgresql+asyncpg://uniassist_admin:uniassist_secure_pass_change_in_production@localhost:5432/uniassist_db"
    )
    USE_SQLITE_FALLBACK: bool = True
    SQLITE_DB_PATH: str = "uniassist_local.db"

    # CORS Configuration
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Azure AI Foundry / Azure OpenAI
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-06-01"
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = "gpt-4o-mini"
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT: str = "text-embedding-3-small"
    AZURE_AI_PROJECT_CONNECTION_STRING: str = ""

    # Azure Document Intelligence
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str = ""
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str = ""

    # Azure AI Search / Foundry IQ (RAG)
    AZURE_SEARCH_ENDPOINT: str = ""
    AZURE_SEARCH_API_KEY: str = ""
    AZURE_SEARCH_INDEX_NAME: str = "uniassist-knowledge-index"

    # Azure Blob Storage
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_DOCUMENTS: str = "university-documents"
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_STORAGE_CONTAINER_TIMETABLES: str = "timetable-uploads"
    AZURE_STORAGE_CONTAINER_STUDENT_FILES: str = "student-uploads"
    AZURE_STORAGE_CONTAINER_RAG: str = "rag-knowledge-base"
    LOCAL_BLOB_STORAGE_DIR: str = "storage_blobs"

    # Azure Key Vault
    AZURE_KEY_VAULT_URL: str = ""
    USE_AZURE_KEY_VAULT: bool = False

    # Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING: str = ""
    ENABLE_APP_INSIGHTS: bool = False

    # Default Seed Credentials
    SEED_DEMO_DATA: bool = True
    ADMIN_DEFAULT_EMAIL: str = "admin@example.com"
    ADMIN_DEFAULT_PASSWORD: str = "AdminPassword123!"
    STUDENT_DEFAULT_EMAIL: str = "student@example.com"
    STUDENT_DEFAULT_PASSWORD: str = "StudentPassword123!"
    FACULTY_DEFAULT_EMAIL: str = "faculty@example.com"
    FACULTY_DEFAULT_PASSWORD: str = "FacultyPassword123!"


settings = Settings()
