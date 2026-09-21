"""
AI Chat Endpoint — UniAssist AI Agent interface.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.agents.uniassist_agent import process_chat
from app.schemas.response import StandardResponse
from app.schemas.student import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/message", response_model=StandardResponse[ChatResponse], tags=["AI Chat"])
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to UniAssist AI. The agent classifies intent, performs RAG
    retrieval from Azure AI Search, synthesizes a grounded response via Azure
    OpenAI, and returns the answer with source citations.

    Works fully with mock fallbacks when Azure credentials are not configured.
    """
    response = await process_chat(request, current_user, db)

    return StandardResponse(
        success=True,
        data=response,
        message="AI response generated successfully.",
    )
