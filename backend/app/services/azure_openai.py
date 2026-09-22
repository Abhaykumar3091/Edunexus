"""
Azure OpenAI Service — Client wrapper with RAG-grounded responses.

Flow:
  1. Search Azure AI Search index + Blob Storage for relevant document chunks.
  2. Inject the retrieved chunks into the system prompt as grounding context.
  3. Call Azure OpenAI to generate a response grounded in the retrieved content.
  4. If Azure OpenAI is not configured, return a structured mock response.
"""
import logging
from typing import List

from app.core.config import settings
from app.schemas.student import ChatMessage, CitationSource

logger = logging.getLogger(__name__)


def _is_configured() -> bool:
    return bool(settings.AZURE_OPENAI_ENDPOINT and settings.AZURE_OPENAI_API_KEY)


def _mock_response(user_message: str) -> dict:
    """Return a deterministic mock AI response for common question categories."""
    msg = user_message.lower()



    if any(k in msg for k in ["exam", "examination", "mid-term", "end-term", "datesheet"]):
        return {
            "answer": (
                "Examination schedules are announced by the Controller of Examinations at least "
                "**30 days** before the examination date, as per **Examination Ordinance Section 4.1**. "
                "Students must carry their admit card (Hall Ticket) and university ID card to the "
                "examination hall. Use of electronic devices is strictly prohibited. Seating arrangements "
                "are displayed on the notice board and the student portal 48 hours before each examination."
            ),
            "sources": [
                {"title": "Examination Ordinance, Section 4.1", "snippet": "Schedule announced 30 days before examination.", "source_type": "mock"},
                {"title": "Examination Hall Rules 2024", "snippet": "Admit card and ID card mandatory. No electronic devices.", "source_type": "mock"},
            ],
            "intent": "exam_policy",
        }
    if any(k in msg for k in ["hostel", "accommodation", "room", "apply hostel"]):
        return {
            "answer": (
                "Hostel accommodation is available for eligible students as per the **University Hostel Rules 2024 (Chapter 3)**. "
                "Applications must be submitted online through the student portal before the last date announced each semester. "
                "Allotment is based on distance from hometown (preference to students from >100 km), academic performance, "
                "and available capacity. Students are bound by the hostel code of conduct and curfew timings."
            ),
            "sources": [
                {"title": "University Hostel Rules 2024, Chapter 3", "snippet": "Allotment based on distance and academic merit.", "source_type": "mock"},
                {"title": "Hostel Application Guidelines", "snippet": "Online application via student portal before due date.", "source_type": "mock"},
            ],
            "intent": "hostel_policy",
        }
    elif any(k in msg for k in ["scholarship", "financial aid", "merit", "stipend"]):
        return {
            "answer": (
                "The university offers several scholarship schemes under the **Student Financial Assistance Policy 2024**: "
                "**Merit Scholarship** for top 5% students (25% tuition waiver), **Need-Based Grant** for students with "
                "annual family income below ₹5 lakh (up to 50% waiver), and **Sports Excellence Award** for national/state "
                "level sports achievers. Applications open in July and December each year through the Dean of Student Welfare office."
            ),
            "sources": [
                {"title": "Student Financial Assistance Policy 2024", "snippet": "Merit scholarship for top 5% — 25% tuition waiver.", "source_type": "mock"},
                {"title": "Need-Based Grant Criteria", "snippet": "Income below ₹5L eligible for up to 50% waiver.", "source_type": "mock"},
            ],
            "intent": "scholarship_policy",
        }
    else:
        return {
            "answer": (
                "Welcome to UniAssist AI! I can help you with:\n\n"
                "• 📚 **Fee Structure & Tuition** — check course fee schedules and payment details\n"
                "• 🏠 **Hostel Regulations** — room allotment, silence hours, and mess guidelines\n"
                "• 📝 **Examinations & Grading** — ordinance rules, attendance criteria, and date sheets\n"
                "• 🎓 **Scholarships** — merit scholarships and financial assistance schemes\n\n"
                "Please ask me a question and I will look it up in the official university knowledge base."
            ),
            "sources": [],
            "intent": "general",
        }


async def _retrieve_rag_context(user_message: str) -> tuple[str, list[dict]]:
    """
    Retrieve relevant document chunks from Azure AI Search and Blob Storage.
    Returns (context_text, sources_list).
    """
    all_sources: list[dict] = []
    context_chunks: list[str] = []

    # 1. Try Azure AI Search index
    try:
        from app.services.azure_search import search_knowledge_base
        search_results = await search_knowledge_base(user_message, top_k=5)
        for src in search_results:
            snippet = getattr(src, "snippet", "") or getattr(src, "chunk_text", "") or ""
            title = getattr(src, "title", "") or getattr(src, "document_title", "") or "Knowledge Document"
            source_type = getattr(src, "source_type", "rag_document")
            if snippet.strip():
                context_chunks.append(f"[Source: {title}]\n{snippet}")
                all_sources.append({
                    "title": title,
                    "snippet": snippet[:600],
                    "source_type": source_type,
                })
    except Exception as exc:
        logger.warning("Azure AI Search retrieval failed: %s", exc)

    # 2. Try Blob Storage direct search (Approach B — fetches & caches blob text)
    try:
        from app.services.blob_qa_service import search_blobs_for_answer
        blob_results = await search_blobs_for_answer(user_message, top_k=4)
        for src in blob_results:
            snippet = getattr(src, "snippet", "") or getattr(src, "chunk_text", "") or ""
            title = getattr(src, "title", "") or getattr(src, "document_title", "") or "Blob Document"
            source_type = getattr(src, "source_type", "blob_document")
            if snippet.strip():
                context_chunks.append(f"[Source: {title}]\n{snippet}")
                all_sources.append({
                    "title": title,
                    "snippet": snippet[:600],
                    "source_type": source_type,
                })
    except Exception as exc:
        logger.warning("Blob QA retrieval failed: %s", exc)

    # Deduplicate citation sources by title for clean frontend presentation
    seen_titles = set()
    unique_sources = []
    for src in all_sources:
        key = src["title"].lower().strip()
        if key not in seen_titles:
            seen_titles.add(key)
            unique_sources.append(src)

    # Use all retrieved chunks (up to top 8) for the grounding prompt
    context_text = "\n\n---\n\n".join(context_chunks[:8]) if context_chunks else ""
    logger.info("RAG retrieval: %d chunks, %d unique sources for query: '%s'", len(context_chunks), len(unique_sources), user_message[:80])
    return context_text, unique_sources


async def get_ai_response(user_message: str, history: List[ChatMessage]) -> dict:
    """
    Get AI response grounded in RAG-retrieved documents from Azure OpenAI.
    Falls back to mock if Azure OpenAI is not configured.
    Returns dict with keys: answer, sources, intent.
    """
    if not _is_configured():
        logger.info("Azure OpenAI not configured — returning structured mock response.")
        return _mock_response(user_message)

    try:
        from openai import AsyncAzureOpenAI

        # ── Step 1: Retrieve relevant document context via RAG ──
        rag_context, rag_sources = await _retrieve_rag_context(user_message)

        # ── Step 2: Build system prompt with grounding context ──
        if rag_context:
            system_content = (
                "You are UniAssist AI, the official university student support assistant. "
                "Answer questions about university policies, academic regulations, hostel rules, "
                "and scholarships ONLY based on the KNOWLEDGE BASE provided below.\n\n"
                "RULES:\n"
                "- Answer ONLY from the knowledge base content provided. Do NOT use your general training data.\n"
                "- Always cite the specific document title or section where you found the answer.\n"
                "- If the knowledge base does not contain the answer, say: "
                "'I could not find specific information about this in the university knowledge base. "
                "Please contact the relevant department for assistance.'\n"
                "- Never speculate or fabricate information.\n\n"
                "--- UNIVERSITY KNOWLEDGE BASE ---\n"
                f"{rag_context}\n"
                "--- END KNOWLEDGE BASE ---"
            )
        else:
            system_content = (
                "You are UniAssist AI, the official university student support assistant. "
                "Answer questions about university policies, academic regulations, hostel rules, "
                "and scholarships ONLY based on the provided knowledge. "
                "Always cite the specific regulation or policy document. "
                "If you cannot find the answer in the knowledge base, say so explicitly "
                "and direct the student to the appropriate department. Never speculate."
            )

        client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

        messages = [{"role": "system", "content": system_content}]

        for h in history[-6:]:  # last 6 messages for context
            messages.append({"role": h.role, "content": h.content})

        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=messages,
            temperature=0.1,
            max_tokens=1000,
        )

        answer = response.choices[0].message.content or "No response generated."

        # ── Step 3: Return answer with RAG sources ──
        if rag_sources:
            return {
                "answer": answer,
                "sources": rag_sources,
                "intent": "rag_grounded",
            }
        else:
            return {
                "answer": answer,
                "sources": [{"title": "Azure OpenAI Response", "snippet": "Generated by Azure OpenAI", "source_type": "azure_openai"}],
                "intent": "general",
            }

    except Exception as exc:
        logger.error("Azure OpenAI call failed: %s — falling back to mock.", exc)
        return _mock_response(user_message)
