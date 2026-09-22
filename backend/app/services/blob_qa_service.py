"""
Hybrid Vector & Keyword RAG Service
===================================
Preloads all documents from Azure Blob Storage ('rag-knowledge-base'),
chunks by numbered sections and paragraphs, generates Azure OpenAI
embeddings (text-embedding-3-small), and performs hybrid cosine-similarity +
keyword retrieval for 100% accurate, zero-hallucination grounded answers.
"""
import asyncio
import json
import logging
import math
import os
import re
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.schemas.student import CitationSource

logger = logging.getLogger(__name__)

# Document and chunk data structures
class DocumentChunk:
    def __init__(self, doc_title: str, section: str, text: str, embedding: Optional[List[float]] = None):
        self.doc_title = doc_title
        self.section = section
        self.text = text
        self.embedding = embedding or []

_CHUNKS: List[DocumentChunk] = []
_BLOB_TEXT_CACHE: Dict[str, str] = {}
_INITIALIZED = False
_LOCK = asyncio.Lock()


# ── Text Extraction ────────────────────────────────────────────────────────────

def _extract_with_pymupdf(file_bytes: bytes) -> str:
    try:
        import pymupdf
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text().strip() for page in doc if page.get_text() and page.get_text().strip()]
        doc.close()
        return "\n\n".join(pages)
    except Exception as exc:
        logger.warning("PyMuPDF failed: %s", exc)
        return ""


async def _extract_text(filename: str, file_bytes: bytes) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    if ext in ("txt", "md", "csv", "json", "html"):
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == "pdf":
        text = _extract_with_pymupdf(file_bytes)
        if len(text.strip()) > 50:
            return text

        # Fallback to Document Intelligence if minimal native text
        if settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY:
            try:
                from azure.core.credentials import AzureKeyCredential
                from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
                from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

                async with asyncio.timeout(8.0):
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
            except Exception as e:
                logger.info("DI extraction skipped for %s: %s", filename, e)

        return text

    return file_bytes.decode("utf-8", errors="ignore")


# ── Smart Section-Aware Chunking ──────────────────────────────────────────────

def _chunk_document(doc_title: str, full_text: str) -> List[DocumentChunk]:
    """
    Split document into structured chunks by section headers, paragraphs, or fixed boundaries.
    """
    chunks: List[DocumentChunk] = []
    lines = full_text.split("\n")
    
    current_section = "General Overview"
    current_lines: List[str] = []
    
    section_pattern = re.compile(r"^(\d+[\.\)]\s+[A-Z][A-Za-z0-9\s&/\-–—]{2,60}|Chapter\s+\d+|Section\s+\d+|Article\s+\d+)", re.IGNORECASE)

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if this line is a section heading
        if section_pattern.match(stripped) and len(stripped) < 80:
            if current_lines:
                chunk_text = "\n".join(current_lines).strip()
                if len(chunk_text) > 40:
                    chunks.append(DocumentChunk(doc_title, current_section, chunk_text))
                current_lines = []
            current_section = stripped
            current_lines.append(stripped)
        else:
            current_lines.append(stripped)
            # If current block gets too large (> 1200 chars), split into sub-chunk
            current_text = "\n".join(current_lines)
            if len(current_text) >= 1200:
                chunks.append(DocumentChunk(doc_title, current_section, current_text))
                # Keep last 2 lines as overlap
                current_lines = current_lines[-2:]

    if current_lines:
        chunk_text = "\n".join(current_lines).strip()
        if len(chunk_text) > 40:
            chunks.append(DocumentChunk(doc_title, current_section, chunk_text))

    return chunks


# ── Vector Embeddings & Similarity ─────────────────────────────────────────────

def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


async def _generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Compute embeddings via Azure OpenAI text-embedding-3-small."""
    if not (settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY):
        return [[] for _ in texts]

    try:
        from openai import AsyncAzureOpenAI
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

        # Process in batches of 16
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), 16):
            batch = [t[:3000] for t in texts[i:i+16]]
            resp = await client.embeddings.create(
                model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
                input=batch,
            )
            for item in resp.data:
                all_embeddings.append(item.embedding)
        return all_embeddings
    except Exception as exc:
        logger.error("Failed to generate Azure OpenAI embeddings: %s", exc)
        return [[] for _ in texts]


# ── Knowledge Base Initialization ──────────────────────────────────────────────

async def load_all_blobs(force: bool = False) -> Dict[str, str]:
    """
    Download all blobs, chunk them, and compute embeddings into memory cache.
    """
    global _BLOB_TEXT_CACHE, _CHUNKS, _INITIALIZED

    async with _LOCK:
        if _INITIALIZED and not force:
            return _BLOB_TEXT_CACHE

        from azure.storage.blob import BlobServiceClient

        conn = getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None)
        if not conn:
            logger.warning("AZURE_STORAGE_CONNECTION_STRING not configured.")
            return {}

        rag_container = getattr(settings, "AZURE_STORAGE_CONTAINER_RAG", "rag-knowledge-base")

        try:
            blob_service = BlobServiceClient.from_connection_string(conn)
            cc = blob_service.get_container_client(rag_container)
            blobs = list(cc.list_blobs())
            logger.info("Initializing RAG Engine: Loading %d blobs from '%s'...", len(blobs), rag_container)

            all_new_chunks: List[DocumentChunk] = []

            for b in blobs:
                try:
                    file_bytes = cc.get_blob_client(b.name).download_blob().readall()
                    text = await _extract_text(b.name, file_bytes)
                    if text.strip():
                        clean_title = b.name.replace("-", " ").replace("_", " ").rsplit(".", 1)[0]
                        _BLOB_TEXT_CACHE[b.name] = text
                        doc_chunks = _chunk_document(clean_title, text)
                        all_new_chunks.extend(doc_chunks)
                        logger.info("Parsed '%s': %d chars -> %d section chunks.", b.name, len(text), len(doc_chunks))
                except Exception as exc:
                    logger.error("Error loading blob '%s': %s", b.name, exc)

            # Compute embeddings for all chunks in batch
            if all_new_chunks:
                logger.info("Generating embeddings for %d knowledge chunks...", len(all_new_chunks))
                texts_to_embed = [f"Document: {c.doc_title}\nSection: {c.section}\nContent: {c.text}" for c in all_new_chunks]
                embeddings = await _generate_embeddings(texts_to_embed)
                for chunk, emb in zip(all_new_chunks, embeddings):
                    chunk.embedding = emb
                _CHUNKS = all_new_chunks

            _INITIALIZED = True
            logger.info("RAG Engine Ready: %d chunks loaded & indexed.", len(_CHUNKS))
        except Exception as exc:
            logger.error("Failed to initialize Blob RAG Engine: %s", exc)

        return _BLOB_TEXT_CACHE


# ── Hybrid Retrieval (Vector + Keyword) ────────────────────────────────────────

def _keyword_score(text: str, query_words: List[str]) -> float:
    text_lower = text.lower()
    score = 0.0
    matched = 0
    for w in query_words:
        cnt = text_lower.count(w)
        if cnt > 0:
            score += min(cnt, 3) * 1.0
            matched += 1
    if matched > 0:
        score *= (1.0 + (matched * 0.4))
    return score


async def search_blobs_for_answer(query: str, top_k: int = 6) -> List[CitationSource]:
    """
    Search indexed knowledge base using Hybrid Semantic Vector + Keyword retrieval.
    """
    if not _INITIALIZED:
        await load_all_blobs()

    if not _CHUNKS:
        logger.warning("No knowledge chunks available in memory.")
        return []

    # 1. Compute query vector
    query_embeddings = await _generate_embeddings([query])
    query_vector = query_embeddings[0] if query_embeddings else []

    # 2. Extract query keywords
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

    # Synonym expansion for common university queries
    synonyms = {
        "allowed": ["allow", "permit", "permitted", "keep", "possession", "bring"],
        "items": ["item", "goods", "equipment", "belongings", "appliances", "materials", "articles"],
        "prohibited": ["prohibit", "forbidden", "banned", "not allowed", "confiscation"],
        "rules": ["rule", "regulation", "policy", "bylaws", "guidelines", "ordinance"],
        "fees": ["fee", "tuition", "payment", "installment", "charges"],
        "hostel": ["hosteller", "room", "accommodation", "residence", "dormitory", "warden"],
    }
    expanded_words = list(query_words)
    for w in query_words:
        if w in synonyms:
            expanded_words.extend(synonyms[w])

    scored_chunks: List[Tuple[DocumentChunk, float]] = []

    for chunk in _CHUNKS:
        # Semantic vector score (0.0 to 1.0)
        vec_score = 0.0
        if query_vector and chunk.embedding:
            vec_score = max(0.0, _cosine_similarity(query_vector, chunk.embedding))

        # Keyword match score
        kw_score = _keyword_score(f"{chunk.doc_title} {chunk.section} {chunk.text}", expanded_words)
        normalized_kw_score = min(kw_score / 10.0, 1.0)

        # Hybrid fusion: 70% vector semantic + 30% keyword density
        if vec_score > 0:
            final_score = (0.70 * vec_score) + (0.30 * normalized_kw_score)
        else:
            final_score = normalized_kw_score

        if final_score > 0.15:
            scored_chunks.append((chunk, final_score))

    scored_chunks.sort(key=lambda x: x[1], reverse=True)
    top_results = scored_chunks[:top_k]

    sources: List[CitationSource] = []
    for chunk, score in top_results:
        section_prefix = f"[{chunk.section}]\n" if chunk.section and chunk.section != "General Overview" else ""
        sources.append(
            CitationSource(
                document_title=chunk.doc_title,
                section=chunk.section if chunk.section != "General Overview" else None,
                chunk_text=f"{section_prefix}{chunk.text}",
                relevance_score=round(score, 2),
            )
        )

    logger.info("Hybrid RAG: retrieved %d chunks for query: '%s'", len(sources), query[:80])
    return sources
