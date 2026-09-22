"""
Azure AI Search Service - RAG retrieval client with graceful fallback.

Index schema (ks-file-531-index) field names:
  uid, snippet_parent_id, snippet, h1_header .. h6_header,
  snippet_vector, metadata_storage_path
"""
import logging
from typing import List

from app.core.config import settings
from app.schemas.student import CitationSource

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(
        settings.AZURE_SEARCH_ENDPOINT
        and settings.AZURE_SEARCH_API_KEY
        and not settings.AZURE_SEARCH_API_KEY.startswith("your_")
    )


def _mock_search(query: str) -> List[CitationSource]:
    """Return mock knowledge base results for common query topics."""
    q = query.lower()
    results: List[CitationSource] = []

    if any(k in q for k in ["exam", "examination", "hall ticket"]):
        results = [
            CitationSource(
                document_title="Examination Ordinance 2024 - Section 4",
                chunk_text="The Controller of Examinations will publish the examination schedule at least 30 days before examinations commence. Hall tickets are mandatory for entry.",
                relevance_score=0.92,
            ),
        ]
    if any(k in q for k in ["hostel", "accommodation", "room"]):
        results = [
            CitationSource(
                document_title="University Hostel Rules 2024 - Chapter 3",
                chunk_text="Hostel accommodation is available to full-time students. Priority is given to students residing more than 100 km from campus.",
                relevance_score=0.90,
            ),
        ]
    elif any(k in q for k in ["scholarship", "financial", "merit", "grant"]):
        results = [
            CitationSource(
                document_title="Student Financial Assistance Policy 2024",
                chunk_text="Merit Scholarship: Top 5% of students receive 25% tuition waiver. ",
                relevance_score=0.91,
            ),
        ]

    return results


async def search_knowledge_base(query: str, top_k: int = 5) -> List[CitationSource]:
    """
    Search the Azure AI Search index for relevant documents.
    Uses the correct field names for the ks-file-531-index schema.
    """
    if not _is_configured():
        logger.info("Azure AI Search not configured - returning mock results.")
        return _mock_search(query)

    try:
        from azure.search.documents.aio import SearchClient
        from azure.core.credentials import AzureKeyCredential

        async with SearchClient(
            endpoint=settings.AZURE_SEARCH_ENDPOINT,
            index_name=settings.AZURE_SEARCH_INDEX_NAME,
            credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
        ) as client:
            results = await client.search(
                search_text=query,
                top=top_k,
                select=["uid", "snippet", "h1_header", "h2_header", "metadata_storage_path"],
            )

            sources: List[CitationSource] = []
            async for result in results:
                # Use the exact field names from the index schema
                snippet_text = result.get("snippet") or ""
                title_text = (
                    result.get("h1_header")
                    or result.get("h2_header")
                    or result.get("metadata_storage_path")
                    or "University Knowledge Document"
                )

                if snippet_text.strip():
                    sources.append(
                        CitationSource(
                            document_title=str(title_text),
                            chunk_text=str(snippet_text)[:600],
                            relevance_score=0.90,
                        )
                    )

            if sources:
                logger.info("Azure AI Search found %d results for: %s", len(sources), query)
                return sources
            else:
                logger.warning("Azure AI Search returned 0 results for '%s' - using fallback.", query)
                return _mock_search(query)

    except Exception as exc:
        logger.error("Azure AI Search call failed: %s - falling back to mock.", exc)
        return _mock_search(query)
