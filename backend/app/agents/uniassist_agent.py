import uuid
import logging
from typing import List
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.student import ChatRequest, ChatResponse, CitationSource
from app.services.azure_openai import get_ai_response

logger = logging.getLogger(__name__)


async def process_chat(request: ChatRequest, current_user: User, db: Session) -> ChatResponse:
    conv_id = request.conversation_id or str(uuid.uuid4())
    message = request.message

    # Get AI response grounded in RAG-retrieved documents
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

    # Tag which data sources were used for transparency
    intent = ai_result.get("intent", "general")
    if intent == "rag_grounded":
        # Identify unique source types
        source_types = set(s.get("source_type", "") for s in raw_sources)
        if "rag_document" in source_types:
            data_sources.append("Azure AI Search Knowledge Base")
        if "blob_document" in source_types:
            data_sources.append("Azure Blob Storage Documents")

    return ChatResponse(
        message=answer,
        sources=sources,
        data_sources=data_sources,
        conversation_id=conv_id,
    )
