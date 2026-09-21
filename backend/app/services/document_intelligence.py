"""
Azure Document Intelligence & Document Q&A Service.

Extracts text, paragraphs, tables, and page layout from uploaded files (PDF, TXT, DOCX, CSV)
and provides grounded Q&A answering questions from anywhere in the document using Azure OpenAI.
"""
import io
import logging
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence.aio import DocumentIntelligenceClient

from app.core.config import settings

logger = logging.getLogger(__name__)

# Active document sessions stored in memory: doc_id -> DocumentData
DOCUMENT_STORE: Dict[str, Dict[str, Any]] = {}


class DocumentSection(BaseModel):
    page_number: int
    title: str
    content: str


class AnalyzedDocument(BaseModel):
    document_id: str
    filename: str
    file_type: str
    page_count: int
    word_count: int
    summary_preview: str
    sections: List[DocumentSection]


async def parse_text_content(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """Parse text, layout, and sections using Azure Document Intelligence."""
    sections: List[DocumentSection] = []
    full_text = ""
    page_count = 1

    if settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY:
        try:
            client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY)
            )
            async with client:
                poller = await client.begin_analyze_document(
                    "prebuilt-layout", 
                    file_bytes, 
                    content_type="application/octet-stream"
                )
                result = await poller.result()
            
            if result.pages:
                page_count = len(result.pages)
            full_text = result.content or ""
            
            if result.paragraphs:
                for idx, para in enumerate(result.paragraphs):
                    page_num = 1
                    if para.bounding_regions:
                        page_num = para.bounding_regions[0].page_number
                    
                    # Group short paragraphs or just use role if available
                    title = getattr(para, 'role', f"Section {idx + 1}") or f"Section {idx + 1}"
                    
                    sections.append(
                        DocumentSection(
                            page_number=page_num,
                            title=title,
                            content=para.content,
                        )
                    )
            else:
                sections.append(DocumentSection(page_number=1, title="Document Content", content=full_text[:2000]))
                
        except Exception as e:
            logger.error("Azure Document Intelligence failed: %s", e)
            raise e
    else:
        logger.warning("Azure Document Intelligence not configured. Falling back to simple text decode.")
        raw_text = file_bytes.decode("utf-8", errors="ignore")
        full_text = raw_text
        sections.append(DocumentSection(page_number=1, title="Document Content", content=raw_text[:2000]))

    words = full_text.split()
    summary_preview = (
        " ".join(words[:50]) + ("..." if len(words) > 50 else "") if words else "Empty document."
    )

    return {
        "page_count": max(page_count, 1),
        "word_count": len(words),
        "full_text": full_text.strip(),
        "summary_preview": summary_preview,
        "sections": sections,
    }


async def analyze_uploaded_document(filename: str, file_bytes: bytes) -> AnalyzedDocument:
    """Analyze and index an uploaded document for interactive Q&A."""
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    parsed = await parse_text_content(filename, file_bytes)

    doc_data = {
        "document_id": doc_id,
        "filename": filename,
        "file_type": filename.split(".")[-1].upper() if "." in filename else "TXT",
        "page_count": parsed["page_count"],
        "word_count": parsed["word_count"],
        "full_text": parsed["full_text"],
        "summary_preview": parsed["summary_preview"],
        "sections": parsed["sections"],
    }

    DOCUMENT_STORE[doc_id] = doc_data
    logger.info("Document analyzed and stored: id=%s, name=%s, words=%d", doc_id, filename, parsed["word_count"])

    return AnalyzedDocument(
        document_id=doc_id,
        filename=filename,
        file_type=doc_data["file_type"],
        page_count=doc_data["page_count"],
        word_count=doc_data["word_count"],
        summary_preview=doc_data["summary_preview"],
        sections=parsed["sections"][:10],  # send top sections preview
    )


async def ask_document_question(
    document_id: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Answer questions strictly based on the content of the specified uploaded document.
    """
    doc = DOCUMENT_STORE.get(document_id)
    if not doc:
        return {
            "answer": "The requested document session has expired or was not found. Please re-upload the document.",
            "citations": [],
            "found": False,
        }

    full_text = doc["full_text"]
    filename = doc["filename"]

    # Call Azure OpenAI with document grounding
    try:
        from openai import AsyncAzureOpenAI

        if settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY and not settings.AZURE_OPENAI_API_KEY.startswith("your_"):
            client = AsyncAzureOpenAI(
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version=settings.AZURE_OPENAI_API_VERSION,
            )

            system_prompt = (
                f"You are UniAssist Document Intelligence AI. You are analyzing the uploaded document: '{filename}'.\n"
                f"Answer the user's question accurately and ONLY based on the text provided below.\n"
                f"If the answer is found, state the answer clearly and cite the exact phrase or section from the document.\n"
                f"If the information is not in the document, state: 'The provided document does not mention information regarding this question.'\n\n"
                f"--- DOCUMENT CONTENT ---\n{full_text[:12000]}\n--- END DOCUMENT CONTENT ---"
            )

            messages = [{"role": "system", "content": system_prompt}]
            if history:
                for h in history[-4:]:
                    messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": question})

            response = await client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=messages,
                temperature=0.1,
                max_tokens=800,
            )

            answer = response.choices[0].message.content or "No answer generated."

            # Find matching snippet for citation
            q_lower = question.lower()
            matching_snippet = ""
            for s in doc["sections"]:
                if any(w in s.content.lower() for w in q_lower.split() if len(w) > 3):
                    matching_snippet = s.content[:200]
                    break
            if not matching_snippet and doc["sections"]:
                matching_snippet = doc["sections"][0].content[:200]

            return {
                "answer": answer,
                "citations": [
                    {
                        "source_file": filename,
                        "snippet": matching_snippet,
                        "document_id": document_id,
                    }
                ],
                "found": True,
            }

    except Exception as e:
        logger.error("Azure OpenAI Document Q&A error: %s", e)

    # Simple fallback if OpenAI is offline
    return {
        "answer": f"Based on '{filename}':\n\n{full_text[:400]}...",
        "citations": [{"source_file": filename, "snippet": full_text[:150], "document_id": document_id}],
        "found": True,
    }
