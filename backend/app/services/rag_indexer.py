"""
RAG Indexer Service
===================
Extracts text from uploaded PDFs, chunks it, generates embeddings,
and pushes each chunk into Azure AI Search so the chatbot can answer from it.

Extraction strategy (tiered by file size):
  - Plain text / TXT / MD  -> direct UTF-8 decode
  - PDF <= 4 MB            -> Azure Document Intelligence (best quality OCR)
  - PDF > 4 MB             -> PyMuPDF (fast, handles large scanned PDFs)
  - DOCX                   -> python-docx (fallback)

Index schema (ks-file-531-index):
  uid, snippet_parent_id, snippet, h1_header..h6_header,
  snippet_vector, metadata_storage_path
"""
import hashlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1500
CHUNK_OVERLAP = 200
DI_MAX_BYTES = 4 * 1024 * 1024   # 4 MB threshold for Document Intelligence


# ── Helpers ────────────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    if not text.strip():
        return []
    chunks: List[str] = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start += chunk_size - overlap
    return chunks


def _file_uid(filename: str, chunk_index: int) -> str:
    raw = f"{filename}__chunk_{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


# ── Text extraction ────────────────────────────────────────────────────────────

def _extract_with_pymupdf(file_bytes: bytes) -> str:
    """Fast, complete multi-page text extraction using PyMuPDF - handles any number of pages."""
    try:
        import pymupdf  # type: ignore
        doc = pymupdf.open(stream=file_bytes, filetype="pdf")
        page_count = len(doc)
        pages_text = []
        for idx, page in enumerate(doc):
            t = page.get_text()
            if t.strip():
                pages_text.append(f"=== PAGE {idx + 1} ===\n{t.strip()}")
        doc.close()
        result = "\n\n".join(pages_text)
        logger.info("PyMuPDF extracted %d pages, %d chars.", page_count, len(result))
        return result
    except Exception as exc:
        logger.error("PyMuPDF extraction failed: %s", exc)
        return ""


async def _extract_with_document_intelligence(filename: str, file_bytes: bytes) -> str:
    """High-quality OCR via Azure Document Intelligence (SDK v1.0+, <= 4MB)."""
    from app.core.config import settings
    from azure.core.credentials import AzureKeyCredential
    from azure.ai.documentintelligence.aio import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest

    if not (settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY):
        return ""

    try:
        client = DocumentIntelligenceClient(
            endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
            credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
        )
        async with client:
            poller = await client.begin_analyze_document(
                model_id="prebuilt-read",
                body=AnalyzeDocumentRequest(bytes_source=file_bytes),
            )
            result = await poller.result()

        paragraphs = []
        if hasattr(result, "paragraphs") and result.paragraphs:
            for p in result.paragraphs:
                c = getattr(p, "content", None)
                if c:
                    paragraphs.append(c.strip())
        elif hasattr(result, "pages") and result.pages:
            for page in result.pages:
                for line in getattr(page, "lines", []):
                    c = getattr(line, "content", None)
                    if c:
                        paragraphs.append(c.strip())

        text = "\n".join(paragraphs)
        logger.info("Document Intelligence extracted %d chars from '%s'.", len(text), filename)
        return text
    except Exception as exc:
        logger.warning("Document Intelligence failed for '%s': %s. Falling back.", filename, exc)
        return ""


async def extract_text_from_bytes(filename: str, file_bytes: bytes) -> str:
    """
    Complete multi-page extraction:
      1. Plain text -> direct decode
      2. PDF -> PyMuPDF (extracts all 1-100+ pages uncapped)
      3. Scanned PDF fallback -> Azure Document Intelligence
      4. Other -> PyMuPDF fallback
    """
    ext = filename.lower().rsplit(".", 1)[-1]

    # Plain text
    if ext in ("txt", "md", "csv"):
        return file_bytes.decode("utf-8", errors="ignore")

    if ext == "pdf":
        # PyMuPDF extracts all pages without Azure F0 free-tier page drop
        text = _extract_with_pymupdf(file_bytes)
        if len(text.strip()) > 50:
            logger.info("Extracted %d chars across all pages with PyMuPDF for '%s'", len(text), filename)
            return text

        # If scanned image PDF with no embedded text, fallback to Azure Document Intelligence OCR
        logger.info("PyMuPDF found minimal text; attempting Azure Document Intelligence OCR for '%s'", filename)
        di_text = await _extract_with_document_intelligence(filename, file_bytes)
        if di_text.strip():
            return di_text
        return text

    # DOCX / other - try PyMuPDF anyway
    return _extract_with_pymupdf(file_bytes)


# ── Embeddings ─────────────────────────────────────────────────────────────────

async def _generate_embedding(text: str) -> Optional[List[float]]:
    """Generate vector embedding via Azure OpenAI text-embedding-3-small."""
    from app.core.config import settings

    if not (settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY):
        return None

    try:
        from openai import AsyncAzureOpenAI
        client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION or "2024-06-01",
        )
        deployment = getattr(settings, "AZURE_OPENAI_EMBEDDING_DEPLOYMENT", "text-embedding-3-small")
        response = await client.embeddings.create(model=deployment, input=text[:8000])
        return response.data[0].embedding
    except Exception as exc:
        logger.warning("Embedding generation failed: %s", exc)
        return None


# ── Main pipeline ──────────────────────────────────────────────────────────────

async def index_document_into_search(
    filename: str,
    file_bytes: bytes,
    category: str = "policy",
) -> Dict[str, Any]:
    """
    Full RAG pipeline:
      1. Extract text  (DI for small PDFs, PyMuPDF for large)
      2. Chunk text
      3. Generate embeddings
      4. Upload to Azure AI Search index
    """
    from app.core.config import settings
    from azure.search.documents import SearchClient
    from azure.core.credentials import AzureKeyCredential

    if not (settings.AZURE_SEARCH_ENDPOINT and settings.AZURE_SEARCH_API_KEY):
        logger.warning("Azure AI Search not configured - skipping indexing.")
        return {"indexed_chunks": 0, "filename": filename, "status": "skipped_no_search"}

    full_text = await extract_text_from_bytes(filename, file_bytes)
    if not full_text.strip():
        logger.warning("No text extracted from '%s'.", filename)
        return {"indexed_chunks": 0, "filename": filename, "status": "no_text_extracted"}

    chunks = _chunk_text(full_text)
    logger.info("'%s' -> %d chunks.", filename, len(chunks))

    search_client = SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=settings.AZURE_SEARCH_INDEX_NAME,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
    )

    indexed = 0
    batch: List[Dict[str, Any]] = []

    for i, chunk in enumerate(chunks):
        embedding = await _generate_embedding(chunk)
        doc: Dict[str, Any] = {
            "uid": _file_uid(filename, i),
            "snippet_parent_id": filename,
            "snippet": chunk,
            "h1_header": category.upper(),
            "h2_header": filename,
            "h3_header": None,
            "h4_header": None,
            "h5_header": None,
            "h6_header": None,
            "metadata_storage_path": filename,
        }
        if embedding:
            doc["snippet_vector"] = embedding
        batch.append(doc)

        if len(batch) >= 20:
            try:
                search_client.upload_documents(documents=batch)
                indexed += len(batch)
                logger.info("Uploaded %d chunks so far for '%s'.", indexed, filename)
            except Exception as exc:
                logger.error("Batch upload failed: %s", exc)
            batch = []

    if batch:
        try:
            search_client.upload_documents(documents=batch)
            indexed += len(batch)
        except Exception as exc:
            logger.error("Final batch upload failed: %s", exc)

    logger.info("Indexed %d/%d chunks for '%s'.", indexed, len(chunks), filename)
    return {
        "indexed_chunks": indexed,
        "total_chunks": len(chunks),
        "filename": filename,
        "status": "indexed",
        "text_length": len(full_text),
    }
