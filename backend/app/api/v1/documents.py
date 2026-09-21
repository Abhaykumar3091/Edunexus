import asyncio
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.response import StandardResponse
from app.services import azure_storage
from app.services.document_intelligence import (
    AnalyzedDocument,
    analyze_uploaded_document,
    ask_document_question,
)
from app.services.rag_indexer import index_document_into_search

router = APIRouter(prefix="/documents", tags=["Document Intelligence RAG Storage"])


class DocumentQuestionRequest(BaseModel):
    document_id: str
    question: str
    history: Optional[List[Dict[str, str]]] = []


class DocumentQuestionResponse(BaseModel):
    answer: str
    citations: List[Dict[str, Any]] = []
    found: bool


class RagUploadResponse(BaseModel):
    success: bool
    blob_name: str
    container: str
    url: str
    size_bytes: int
    content_type: str
    rag_container: str
    rag_ready: bool
    metadata: Dict[str, Any]


@router.post("/analyze", response_model=AnalyzedDocument)
async def upload_and_analyze_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_bytes) > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 15MB limit.")

    try:
        await azure_storage.upload_blob(
            file_name=file.filename,
            file_content=file_bytes,
            content_type=file.content_type or "application/octet-stream",
            metadata={"uploaded_by": current_user.email},
        )
        analyzed = await analyze_uploaded_document(file.filename, file_bytes)
        return analyzed
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to analyze document: {str(e)}")


@router.post("/ask", response_model=StandardResponse[DocumentQuestionResponse])
async def ask_question_on_document(
    payload: DocumentQuestionRequest,
    current_user: User = Depends(get_current_user),
):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    result = await ask_document_question(
        document_id=payload.document_id,
        question=payload.question,
        history=payload.history,
    )
    return StandardResponse(success=True, data=result)


@router.post("/upload-rag", response_model=StandardResponse[RagUploadResponse])
async def upload_document_for_rag(
    file: UploadFile = File(...),
    category: str = Form("policy"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided.")

    file_bytes = await file.read()
    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if len(file_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File exceeds 20MB limit.")

    # Step 1: Store in Azure Blob Storage
    res = await azure_storage.store_document_for_rag(
        file_name=file.filename,
        file_content=file_bytes,
        category=category,
        content_type=file.content_type or "application/pdf",
        metadata={
            "uploaded_by_user_id": str(current_user.id),
            "uploaded_by_email": current_user.email,
        },
    )

    if not res.get("success"):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to store document in Azure Blob Storage: {res.get('error')}",
        )

    # Step 2: Extract text & index into Azure AI Search (background task)
    background_tasks.add_task(
        index_document_into_search,
        filename=file.filename,
        file_bytes=file_bytes,
        category=category,
    )

    return StandardResponse(
        success=True,
        data=RagUploadResponse(**res),
        message=f"'{file.filename}' uploaded to Blob Storage and queued for AI Search indexing.",
    )


@router.get("/rag-list", response_model=StandardResponse[List[Dict[str, Any]]])
async def list_rag_documents(
    container: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    blobs = await azure_storage.list_documents(container_name=container)
    return StandardResponse(
        success=True,
        data=blobs,
        message=f"Retrieved {len(blobs)} documents from Azure Blob Storage.",
    )
