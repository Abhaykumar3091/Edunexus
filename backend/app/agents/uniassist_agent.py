import uuid
import logging
from typing import List
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.student_data import Student, Complaint
from app.schemas.student import ChatRequest, ChatResponse, CitationSource
from app.services.azure_openai import get_ai_response

logger = logging.getLogger(__name__)


async def process_chat(request: ChatRequest, current_user: User, db: Session) -> ChatResponse:
    conv_id = request.conversation_id or str(uuid.uuid4())
    message = request.message

    # Get AI or fallback mock response
    ai_result = await get_ai_response(message, request.history or [])
    answer = ai_result.get("answer", "")
    raw_sources = ai_result.get("sources", [])

    sources: List[CitationSource] = []
    for s in raw_sources:
        sources.append(
            CitationSource(
                document_title=s.get("title") or "University Regulation",
                section=s.get("section"),
                chunk_text=s.get("snippet"),
                relevance_score=0.95,
            )
        )

    data_sources: List[str] = []
    # Check if student grievances were referenced
    if any(k in message.lower() for k in ["complaint", "grievance", "ticket", "issue"]):
        student = db.query(Student).filter(Student.user_id == current_user.id).first()
        if student:
            complaints = db.query(Complaint).filter(Complaint.student_id == student.id).all()
            if complaints:
                data_sources.append("Student Grievances DB")
                c_details = ", ".join([f"{c.ticket_id} ({c.status.value})" for c in complaints])
                answer += f"\n\n**Your Registered Grievances:** {c_details}"

    return ChatResponse(
        message=answer,
        sources=sources,
        data_sources=data_sources,
        conversation_id=conv_id,
    )
