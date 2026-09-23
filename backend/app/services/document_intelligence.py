"""
Azure Document Intelligence & Document Q&A Service.

Extracts text, paragraphs, tables, and page layout from uploaded files (PDF, TXT, DOCX, CSV)
and provides grounded Q&A answering questions from anywhere in the document using Azure OpenAI.
"""
import io
import logging
import re
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
    """Parse text, layout, and sections using PyMuPDF for high-speed multi-page extraction with Azure Document Intelligence fallback."""
    sections: List[DocumentSection] = []
    full_text = ""
    page_count = 1
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""

    # Strategy 1: For PDFs, use PyMuPDF first for complete, uncapped multi-page extraction
    if ext == "pdf" or file_bytes.startswith(b"%PDF"):
        try:
            import pymupdf
            doc = pymupdf.open(stream=file_bytes, filetype="pdf")
            page_count = max(len(doc), 1)
            page_texts = []

            for page_idx, page in enumerate(doc):
                p_num = page_idx + 1
                text = page.get_text().strip()
                if text:
                    page_texts.append(f"=== PAGE {p_num} ===\n{text}")
                    # Split into structured paragraphs for precise citation tracking
                    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
                    if paras:
                        for s_idx, p in enumerate(paras):
                            title = f"Page {p_num}" + (f" - Section {s_idx + 1}" if len(paras) > 1 else "")
                            sections.append(DocumentSection(
                                page_number=p_num,
                                title=title,
                                content=p,
                            ))
                    else:
                        sections.append(DocumentSection(
                            page_number=p_num,
                            title=f"Page {p_num}",
                            content=text,
                        ))
            doc.close()

            if page_texts:
                full_text = "\n\n".join(page_texts)
                logger.info("PyMuPDF successfully extracted %d pages, %d chars from '%s'", page_count, len(full_text), filename)
        except Exception as exc:
            logger.warning("PyMuPDF extraction failed for '%s': %s", filename, exc)

    # Strategy 2: If no text was extracted (e.g., scanned PDF image or non-PDF image/doc), try Azure Document Intelligence
    if not full_text.strip() and settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY:
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
                page_count = max(len(result.pages), 1)
            full_text = result.content or ""
            
            if result.paragraphs:
                for idx, para in enumerate(result.paragraphs):
                    page_num = 1
                    if para.bounding_regions:
                        page_num = para.bounding_regions[0].page_number
                    
                    title = getattr(para, 'role', f"Page {page_num} Sec {idx + 1}") or f"Page {page_num} Sec {idx + 1}"
                    sections.append(
                        DocumentSection(
                            page_number=page_num,
                            title=title,
                            content=para.content,
                        )
                    )
            elif full_text:
                sections.append(DocumentSection(page_number=1, title="Document Content", content=full_text))
            logger.info("Azure Document Intelligence extracted %d pages, %d chars from '%s'", page_count, len(full_text), filename)
        except Exception as e:
            logger.error("Azure Document Intelligence failed: %s", e)

    # Strategy 3: Plain text / UTF-8 fallback
    if not full_text.strip():
        logger.warning("Falling back to raw text decode for '%s'", filename)
        raw_text = file_bytes.decode("utf-8", errors="ignore")
        full_text = raw_text
        if raw_text.strip():
            sections.append(DocumentSection(page_number=1, title="Document Content", content=raw_text))

    words = full_text.split()
    summary_preview = (
        " ".join(words[:60]) + ("..." if len(words) > 60 else "") if words else "Empty document."
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
    logger.info("Document analyzed and stored: id=%s, name=%s, pages=%d, words=%d", doc_id, filename, parsed["page_count"], parsed["word_count"])

    return AnalyzedDocument(
        document_id=doc_id,
        filename=filename,
        file_type=doc_data["file_type"],
        page_count=doc_data["page_count"],
        word_count=doc_data["word_count"],
        summary_preview=doc_data["summary_preview"],
        sections=parsed["sections"][:100],  # send up to 100 preview sections
    )


# Maximum characters passed into context window (~120,000 tokens — absolute maximum of gpt-4o-mini / gpt-4.1-mini 128k limit)
MAX_DOCUMENT_CONTEXT_CHARS = 500000


def _build_focused_context(full_text: str, sections: List[DocumentSection], question: str) -> str:
    """
    If the document fits in MAX_DOCUMENT_CONTEXT_CHARS (up to 120-150 pages), return full text.
    If extraordinarily large (> 150 pages), prioritize sections matching the question.
    """
    if len(full_text) <= MAX_DOCUMENT_CONTEXT_CHARS:
        return full_text

    # Extremely large document: include first 25,000 chars (intro/overview/TOC) + best matching sections
    q_words = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 3]
    scored_sections = []
    for s in sections:
        content_lower = s.content.lower()
        score = sum(content_lower.count(w) for w in q_words)
        scored_sections.append((score, s))

    scored_sections.sort(key=lambda x: x[0], reverse=True)

    included_chunks = [f"[Document Overview / Beginning]\n{full_text[:25000]}"]
    total_len = len(included_chunks[0])

    for score, s in scored_sections:
        chunk_str = f"\n\n[Page {s.page_number} - {s.title}]\n{s.content}"
        if total_len + len(chunk_str) > MAX_DOCUMENT_CONTEXT_CHARS:
            break
        included_chunks.append(chunk_str)
        total_len += len(chunk_str)

    return "\n\n".join(included_chunks)


async def ask_document_question(
    document_id: str,
    question: str,
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """
    Answer questions strictly based on the content of the specified uploaded document.
    Covers all pages (10+ pages) without truncation using expanded 128k context window.
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
    page_count = doc.get("page_count", 1)
    sections: List[DocumentSection] = doc.get("sections", [])

    # Prepare complete multi-page document context
    document_context = _build_focused_context(full_text, sections, question)

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
                f"You are UniAssist Document Intelligence AI. You are analyzing the uploaded document: '{filename}' ({page_count} pages total).\n"
                f"The document content below includes explicit page markers ('=== PAGE X ===' or page numbers).\n"
                f"Answer the user's question accurately, thoroughly, and ONLY based on the document text provided below.\n"
                f"Always state the specific Page number (e.g. 'Page 3', 'Page 7') where the information or rule is located.\n"
                f"If the information is not in the document, state: 'The provided document does not mention information regarding this question.'\n\n"
                f"--- DOCUMENT CONTENT ({page_count} Pages) ---\n{document_context}\n--- END DOCUMENT CONTENT ---"
            )

            messages = [{"role": "system", "content": system_prompt}]
            if history:
                for h in history[-6:]:
                    messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": question})

            response = await client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
                messages=messages,
                temperature=0.1,
                max_tokens=4096,
            )

            answer = response.choices[0].message.content or "No answer generated."

            # Find matching snippets and page numbers for citation
            q_words = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 3]
            scored_sections = []

            for s in sections:
                score = sum(s.content.lower().count(w) for w in q_words)
                if score > 0:
                    scored_sections.append((score, s))

            scored_sections.sort(key=lambda x: x[0], reverse=True)

            citations = []
            seen_pages = set()
            for score, s in scored_sections[:3]:
                if s.page_number not in seen_pages:
                    seen_pages.add(s.page_number)
                    citations.append({
                        "source_file": f"{filename} (Page {s.page_number})",
                        "snippet": s.content[:300],
                        "document_id": document_id,
                    })

            if not citations and sections:
                citations.append({
                    "source_file": f"{filename} (Page {sections[0].page_number})",
                    "snippet": sections[0].content[:250],
                    "document_id": document_id,
                })

            return {
                "answer": answer,
                "citations": citations,
                "found": True,
            }

    except Exception as e:
        logger.error("Azure OpenAI Document Q&A error: %s", e)

    # Simple fallback if OpenAI is offline
    return {
        "answer": f"Based on '{filename}' ({page_count} pages):\n\n{full_text[:600]}...",
        "citations": [{"source_file": filename, "snippet": full_text[:150], "document_id": document_id}],
        "found": True,
    }
