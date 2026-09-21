"""
Blob QA Service (Approach B)
=============================
On every chat query, fetches documents directly from Azure Blob Storage,
extracts their text on-demand, and uses that as grounding context for the AI.

Strategy:
- Text is extracted once per server session and cached in memory.
- Scanned & native PDFs use Azure Document Intelligence with multi-page batching + PyMuPDF.
- Plain text files are decoded directly.
- On query: keyword relevance scoring finds the most relevant chunks.
"""
import asyncio
import logging
import re
from typing import Dict, List, Optional, Tuple

from app.schemas.student import CitationSource

logger = logging.getLogger(__name__)

# In-memory cache: blob_name -> full extracted text
_BLOB_TEXT_CACHE: Dict[str, str] = {}
_CACHE_LOADED = False

DI_MAX_BYTES = 10 * 1024 * 1024   # 10 MB


# ── Text extraction ────────────────────────────────────────────────────────────

def _extract_with_pymupdf(file_bytes: bytes) -> str:
    try:
        import pymupdf  # type: ignore
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc if page.get_text().strip()]
        doc.close()
        return "\n".join(pages)
    except Exception as exc:
        logger.error("PyMuPDF failed: %s", exc)
        return ""


async def _extract_with_di(filename: str, file_bytes: bytes) -> str:
    from app.core.config import settings
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    if not (settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY):
        return ""

    total_pages = 1
    try:
        import pymupdf
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        total_pages = len(doc)
        doc.close()
    except Exception:
        pass

    all_texts = []
    # Analyze the most critical first 8 pages in pairs of 2 with spacing to respect F0 tier
    max_pages = min(total_pages, 8)
    page_ranges = []
    for start in range(1, max_pages + 1, 2):
        end = min(start + 1, max_pages)
        page_ranges.append(f"{start}-{end}" if start != end else f"{start}")

    try:
        client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
        )
        async with client:
            for pr in page_ranges:
                try:
                    poller = await client.begin_analyze_document(
                        model_id="prebuilt-read",
                        body=AnalyzeDocumentRequest(bytes_source=file_bytes),
                        pages=pr,
                    )
                    result = await poller.result()
                    if hasattr(result, "content") and result.content:
                        all_texts.append(result.content.strip())
                    await asyncio.sleep(1.5)
                except Exception as page_exc:
                    logger.warning("Document Intelligence page range %s failed for '%s': %s", pr, filename, page_exc)
                    await asyncio.sleep(2)

        return "\n\n".join(all_texts)
    except Exception as exc:
        logger.warning("Document Intelligence failed for '%s': %s", filename, exc)
        return ""


async def _extract_text(filename: str, file_bytes: bytes) -> str:
    """Tiered extraction: plain text -> PyMuPDF (if clean text) -> Document Intelligence OCR."""
    ext = filename.lower().rsplit(".", 1)[-1]

    if ext in ("txt", "md", "csv"):
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == "pdf":
        # 1. Try PyMuPDF text layer first (fast for digitally generated PDFs)
        text = _extract_with_pymupdf(file_bytes)
        if len(text.strip()) > 300:
            logger.info("PyMuPDF extracted %d chars from '%s'.", len(text), filename)
            return text

        # 2. For scanned / image PDFs or sparse text, use Document Intelligence OCR
        if len(file_bytes) <= DI_MAX_BYTES:
            logger.info("'%s' has scanned images/sparse text; running Document Intelligence OCR.", filename)
            di_text = await _extract_with_di(filename, file_bytes)
            if di_text.strip():
                logger.info("Document Intelligence extracted %d chars from '%s'.", len(di_text), filename)
                return di_text

        # Fallback to whatever PyMuPDF got
        return text

    return file_bytes.decode("utf-8", errors="ignore")


# ── Cache management ───────────────────────────────────────────────────────────

async def load_all_blobs(force: bool = False) -> Dict[str, str]:
    """
    Download all blobs from rag-knowledge-base and extract their text.
    Results are cached in memory for the server session.
    Set force=True to reload even if already cached.
    """
    global _BLOB_TEXT_CACHE, _CACHE_LOADED

    if _CACHE_LOADED and not force:
        return _BLOB_TEXT_CACHE

    from app.core.config import settings
    from azure.storage.blob import BlobServiceClient

    conn = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)
    if not conn:
        logger.warning("AZURE_STORAGE_CONNECTION_STRING not set. Blob QA unavailable.")
        return {}

    rag_container = getattr(settings, "AZURE_STORAGE_CONTAINER_RAG", "rag-knowledge-base")

    try:
        blob_service = BlobServiceClient.from_connection_string(conn)
        cc = blob_service.get_container_client(rag_container)
        blobs = list(cc.list_blobs())
        logger.info("Loading %d blobs from '%s' for Blob QA...", len(blobs), rag_container)

        for b in blobs:
            if b.name in _BLOB_TEXT_CACHE and not force:
                continue
            try:
                file_bytes = cc.get_blob_client(b.name).download_blob().readall()
                text = await _extract_text(b.name, file_bytes)
                if text.strip():
                    _BLOB_TEXT_CACHE[b.name] = text
                    logger.info("Cached '%s': %d chars.", b.name, len(text))
                else:
                    logger.warning("No text from '%s'.", b.name)
            except Exception as exc:
                logger.error("Failed to load blob '%s': %s", b.name, exc)

        _CACHE_LOADED = True
        logger.info("Blob QA cache ready: %d documents cached.", len(_BLOB_TEXT_CACHE))
    except Exception as exc:
        logger.error("Failed to connect to Blob Storage: %s", exc)

    return _BLOB_TEXT_CACHE


# ── Relevance scoring ──────────────────────────────────────────────────────────

def _score_chunk(chunk: str, query_words: List[str]) -> int:
    """Score chunk based on keyword matches and density."""
    chunk_lower = chunk.lower()
    score = 0
    for w in query_words:
        if w in chunk_lower:
            score += chunk_lower.count(w) + 1
    return score


def _get_relevant_chunks(
    text: str,
    query: str,
    chunk_size: int = 1000,
    overlap: int = 150,
    top_k: int = 4,
) -> List[str]:
    """Split text into chunks and return the most query-relevant ones."""
    stop = {
        "what", "are", "the", "is", "a", "an", "of", "for", "in", "and",
        "to", "i", "me", "my", "do", "does", "can", "tell", "about", "with",
        "from", "on", "at", "by", "this", "that", "it", "its", "or", "as"
    }
    query_words = [w for w in re.findall(r"\b\w+\b", query.lower()) if w not in stop and len(w) > 2]

    if not query_words:
        query_words = re.findall(r"\b\w+\b", query.lower())

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start += chunk_size - overlap

    scored = [(c, _score_chunk(c, query_words)) for c, score in [(c, _score_chunk(c, query_words)) for c in chunks if c] if score > 0]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [c for c, score in scored[:top_k]]


# ── Main search function ───────────────────────────────────────────────────────

async def search_blobs_for_answer(query: str, top_k: int = 4) -> List[CitationSource]:
    """
    Search all blob documents for content relevant to the query.
    Returns CitationSource objects compatible with the existing chat pipeline.
    """
    blob_texts = await load_all_blobs()

    if not blob_texts:
        logger.warning("No blob texts available for QA.")
        return []

    all_results: List[Tuple[str, str, int]] = []

    stop = {
        "what", "are", "the", "is", "a", "an", "of", "for", "in", "and",
        "to", "i", "me", "my", "do", "does", "can", "tell", "about", "with",
        "from", "on", "at", "by", "this", "that", "it", "its", "or", "as"
    }
    query_words = [w for w in re.findall(r"\b\w+\b", query.lower()) if w not in stop and len(w) > 2]
    if not query_words:
        query_words = re.findall(r"\b\w+\b", query.lower())

    for blob_name, text in blob_texts.items():
        chunks = _get_relevant_chunks(text, query, top_k=4)
        for chunk in chunks:
            score = _score_chunk(chunk, query_words)
            if score > 0:
                all_results.append((blob_name, chunk, score))

    all_results.sort(key=lambda x: x[2], reverse=True)
    top_results = all_results[:top_k]

    sources = []
    for blob_name, chunk, score in top_results:
        clean_title = blob_name.replace("-", " ").replace("_", " ").rsplit(".", 1)[0]
        sources.append(
            CitationSource(
                title=clean_title,
                snippet=chunk[:600],
                source_type="blob_document",
            )
        )

    logger.info("Blob QA found %d relevant chunks for: '%s'", len(sources), query[:60])
    return sources
