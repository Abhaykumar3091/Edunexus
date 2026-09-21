"""
Azure OpenAI Service — Client wrapper with graceful fallback.

If AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are configured, real Azure
OpenAI calls are made. Otherwise a structured mock response is returned so the
app runs fully locally without any Azure credentials.
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
    elif any(k in msg for k in ["complaint", "grievance", "issue", "problem"]):
        return {
            "answer": (
                "Students can raise grievances through the **Grievance Redressal Mechanism (GRC Policy 2023)**. "
                "Submit a complaint via the student portal under 'Raise Complaint'. Each complaint receives a unique "
                "ticket ID (format: CMP-YYYY-NNNNN). The concerned department must acknowledge within **48 hours** "
                "and resolve within **15 working days**. Escalation to the Dean is possible if unresolved within 15 days. "
                "Anonymous complaints are not entertained."
            ),
            "sources": [
                {"title": "GRC Policy 2023", "snippet": "Complaints must be resolved within 15 working days.", "source_type": "mock"},
                {"title": "Grievance Escalation Procedure", "snippet": "Escalate to Dean after 15 working days if unresolved.", "source_type": "mock"},
            ],
            "intent": "complaint_policy",
        }
    else:
        return {
            "answer": (                "📅 **Timetable** — check your weekly class schedule, "
                "📝 **Examinations** — see your exam schedule and seating, "
                "🗣️ **Complaints** — file a grievance or track ticket status, "
                "📚 **University Policies** — hostel regulations, scholarships, and more.\n\n"
                "Please ask me a specific question and I will look it up in the official university knowledge base."
            ),
            "sources": [],
            "intent": "general",
        }


async def get_ai_response(user_message: str, history: List[ChatMessage]) -> dict:
    """
    Get AI response from Azure OpenAI, with fallback to mock.
    Returns dict with keys: answer, sources, intent.
    """
    if not _is_configured():
        logger.info("Azure OpenAI not configured — returning structured mock response.")
        return _mock_response(user_message)

    try:
        from openai import AsyncAzureOpenAI

        client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

        messages = [
            {
                "role": "system",
                "content": (
                    "You are UniAssist AI, the official university student support assistant. "
                    "Answer questions about university policies, academic regulations, hostel rules, "
                    "and scholarships ONLY based on the provided knowledge. "
                    "Always cite the specific regulation or policy document. "
                    "If you cannot find the answer in the knowledge base, say so explicitly "
                    "and direct the student to the appropriate department. Never speculate."
                ),
            }
        ]

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
        return {
            "answer": answer,
            "sources": [{"title": "Azure OpenAI Response", "snippet": "Generated by Azure OpenAI", "source_type": "azure_openai"}],
            "intent": "general",
        }

    except Exception as exc:
        logger.error("Azure OpenAI call failed: %s — falling back to mock.", exc)
        return _mock_response(user_message)
