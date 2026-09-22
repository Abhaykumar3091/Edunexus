"""
Blob QA Service
===============
Fetches documents directly from Azure Blob Storage (container: rag-knowledge-base),
extracts text with PyMuPDF / Document Intelligence, caches in memory,
and retrieves top relevant chunks for grounding AI responses.
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
        pages = []
        for page in doc:
            t = page.get_text()
            if t and t.strip():
                pages.append(t.strip())
        doc.close()
        return "\n\n".join(pages)
    except Exception as exc:
        logger.warning("PyMuPDF extraction skipped/failed: %s", exc)
        return ""


async def _extract_with_di(filename: str, file_bytes: bytes) -> str:
    from app.core.config import settings
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    if not (settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY):
        return ""

    try:
        # Wrap DI in a strict timeout to avoid blocking requests
        async with asyncio.timeout(10.0):
            client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
            )
            async with client:
                poller = await client.begin_analyze_document(
                    model_id="prebuilt-read",
                    body=AnalyzeDocumentRequest(bytes_source=file_bytes),
                    pages="1-4",
                )
                result = await poller.result()
                if hasattr(result, "content") and result.content:
                    return result.content.strip()
    except Exception as exc:
        logger.info("Document Intelligence OCR for '%s' returned: %s", filename, exc)
    return ""


async def _extract_text(filename: str, file_bytes: bytes) -> str:
    """Extract text using PyMuPDF first, falling back to DI OCR if empty."""
    ext = filename.lower().rsplit(".", 1)[-1]

    if ext in ("txt", "md", "csv", "json", "html"):
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == "pdf":
        # 1. Try PyMuPDF native text extraction
        text = _extract_with_pymupdf(file_bytes)
        if len(text.strip()) > 50:
            logger.info("PyMuPDF extracted %d chars from '%s'.", len(text), filename)
            return text

        # 2. Scanned PDF fallback: try Document Intelligence OCR
        if len(file_bytes) <= DI_MAX_BYTES:
            logger.info("'%s' has minimal native text; attempting Document Intelligence OCR...", filename)
            di_text = await _extract_with_di(filename, file_bytes)
            if di_text.strip():
                logger.info("Document Intelligence extracted %d chars from '%s'.", len(di_text), filename)
                return di_text

        return text

    return file_bytes.decode("utf-8", errors="ignore")


# ── Cache management ───────────────────────────────────────────────────────────

async def load_all_blobs(force: bool = False) -> Dict[str, str]:
    """
    Download all blobs from rag-knowledge-base and extract their text into memory cache.
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
        logger.info("Loading %d blobs from container '%s' for Blob QA...", len(blobs), rag_container)

        for b in blobs:
            if b.name in _BLOB_TEXT_CACHE and not force:
                continue
            try:
                file_bytes = cc.get_blob_client(b.name).download_blob().readall()
                text = await _extract_text(b.name, file_bytes)
                if text.strip():
                    _BLOB_TEXT_CACHE[b.name] = text
                    logger.info("Cached '%s' (%d chars).", b.name, len(text))
                else:
                    logger.warning("No text extracted from '%s'.", b.name)
            except Exception as exc:
                logger.error("Failed to download/extract blob '%s': %s", b.name, exc)

        _CACHE_LOADED = True
        logger.info("Blob QA cache ready: %d documents cached.", len(_BLOB_TEXT_CACHE))
    except Exception as exc:
        logger.error("Failed to connect to Azure Blob Storage: %s", exc)

    return _BLOB_TEXT_CACHE


# ── Relevance scoring ──────────────────────────────────────────────────────────

def _score_chunk(chunk: str, query_words: List[str]) -> float:
    """Score chunk based on keyword matches, term diversity, and exact subphrase matching."""
    chunk_lower = chunk.lower()
    matches = 0
    matched_words = 0

    for w in query_words:
        cnt = chunk_lower.count(w)
        if cnt > 0:
            matches += cnt
            matched_words += 1

    if matched_words == 0:
        return 0.0

    # Boost score when multiple different query terms are present in the same chunk
    diversity_multiplier = 1.0 + (matched_words * 0.5)
    return float(matches * diversity_multiplier)


def _get_relevant_chunks(
    text: str,
    query: str,
    chunk_size: int = 1200,
    overlap: int = 200,
    top_k: int = 4,
) -> List[str]:
    """Split document text into overlapping chunks and score relevance."""
    stop = {
        "what", "are", "the", "is", "a", "an", "of", "for", "in", "and",
        "to", "i", "me", "my", "do", "does", "can", "tell", "about", "with",
        "from", "on", "at", "by", "this", "that", "it", "its", "or", "as",
        "how", "much", "please", "give", "show", "know"
    }
    raw_words = re.findall(r"\b\w+\b", query.lower())
    query_words = [w for w in raw_words if w not in stop and len(w) > 1]
    if not query_words:
        query_words = raw_words

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk_content = text[start:end].strip()
        if chunk_content:
            chunks.append(chunk_content)
        if end >= len(text):
            break
        start += chunk_size - overlap

    scored: List[Tuple[str, float]] = []
    for c in chunks:
        score = _score_chunk(c, query_words)
        if score > 0:
            scored.append((c, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [c for c, _ in scored[:top_k]]


# ── Main search function ───────────────────────────────────────────────────────

async def search_blobs_for_answer(query: str, top_k: int = 4) -> List[CitationSource]:
    """
    Search cached blob documents for chunks matching the user query.
    Returns CitationSource objects.
    """
    blob_texts = await load_all_blobs()

    if not blob_texts:
        logger.warning("No blob texts available in memory.")
        return []

    stop = {
        "what", "are", "the", "is", "a", "an", "of", "for", "in", "and",
        "to", "i", "me", "my", "do", "does", "can", "tell", "about", "with",
        "from", "on", "at", "by", "this", "that", "it", "its", "or", "as",
        "how", "much", "please", "give", "show", "know"
    }
    raw_words = re.findall(r"\b\w+\b", query.lower())
    query_words = [w for w in raw_words if w not in stop and len(w) > 1]
    if not query_words:
        query_words = raw_words

    all_results: List[Tuple[str, str, float]] = []

    for blob_name, text in blob_texts.items():
        chunks = _get_relevant_chunks(text, query, top_k=4)
        for chunk in chunks:
            score = _score_chunk(chunk, query_words)
            if score > 0:
                all_results.append((blob_name, chunk, score))

    all_results.sort(key=lambda x: x[2], reverse=True)
    top_results = all_results[:top_k]

    sources: List[CitationSource] = []
    for blob_name, chunk, score in top_results:
        clean_title = blob_name.replace("-", " ").replace("_", " ").rsplit(".", 1)[0]
        sources.append(
            CitationSource(
                document_title=clean_title,
                chunk_text=chunk[:800],
                relevance_score=round(min(score / 10.0, 1.0), 2),
            )
        )

    logger.info("Blob QA found %d relevant chunks for query: '%s'", len(sources), query[:60])
    return sources
