from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.student_data import ComplaintCategory, ComplaintStatus


class CitationSource(BaseModel):
    document_title: str
    section: Optional[str] = None
    chunk_text: Optional[str] = None
    relevance_score: float = 0.0
    url: Optional[str] = None


class StudentBase(BaseModel):
    program: str
    semester: int
    section: str
    batch_year: int
    cgpa: Optional[float] = None


class StudentProfileResponse(StudentBase):
    id: int
    user_id: int
    full_name: str
    email: str
    university_id: str

    class Config:
        from_attributes = True


class ComplaintCreate(BaseModel):
    category: ComplaintCategory
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None


class ComplaintSchema(BaseModel):
    id: int
    ticket_id: str
    category: ComplaintCategory
    title: str
    description: str
    status: ComplaintStatus
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    role: str
    content: str
    sources: Optional[List[CitationSource]] = None
    data_sources: Optional[List[str]] = None
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    message: str
    sources: List[CitationSource] = []
    data_sources: List[str] = []
    conversation_id: str


class AdminStatsSchema(BaseModel):
    total_students: int
    total_complaints: int
    open_complaints: int
    resolved_complaints: int
