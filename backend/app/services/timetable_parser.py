"""
Timetable Parser Service

Extracts structured timetable data from an uploaded image or PDF using:
1. Azure Document Intelligence (prebuilt-layout) -- OCR / table extraction
2. Azure OpenAI (GPT-4o-mini)                   -- structured JSON parsing

Falls back gracefully when Azure credentials are not configured.
"""
import json
import logging
from typing import Any, Dict, List, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

VALID_DAYS = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}


# ---------------------------------------------------------------------------
# Step 1: OCR via Azure Document Intelligence
# ---------------------------------------------------------------------------

async def extract_text_from_document(filename: str, file_bytes: bytes) -> str:
    """Run Azure Document Intelligence prebuilt-layout on the file. Returns raw text."""
    if (
        settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
        and settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
    ):
        try:
            from azure.core.credentials import AzureKeyCredential
            from azure.ai.documentintelligence.aio import DocumentIntelligenceClient

            client = DocumentIntelligenceClient(
                endpoint=settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT,
                credential=AzureKeyCredential(settings.AZURE_DOCUMENT_INTELLIGENCE_KEY),
            )
            async with client:
                poller = await client.begin_analyze_document(
                    "prebuilt-layout",
                    file_bytes,
                    content_type="application/octet-stream",
                )
                result = await poller.result()

            raw_text = result.content or ""
            logger.info("Document Intelligence extracted %d chars from '%s'", len(raw_text), filename)
            return raw_text

        except Exception as exc:
            logger.error("Azure Document Intelligence failed for '%s': %s", filename, exc)
            raise RuntimeError(f"Azure Document Intelligence error: {exc}") from exc
    else:
        logger.warning(
            "Azure Document Intelligence not configured -- falling back to raw text decode for '%s'.",
            filename,
        )
        return file_bytes.decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# Step 2: Structured parse via Azure OpenAI
# ---------------------------------------------------------------------------

_PARSE_SYSTEM_PROMPT = (
    "You are a university timetable parser AI.\n"
    "Given raw text extracted from a timetable image or PDF, extract all class slots and return\n"
    "them ONLY as a JSON array (no markdown, no prose).\n\n"
    "Each element must have exactly these keys:\n"
    "  day         - string, one of: Monday Tuesday Wednesday Thursday Friday Saturday Sunday\n"
    "  subject     - string, full subject/course name\n"
    "  code        - string, course code (e.g. CS301) or \"\" if not found\n"
    "  faculty     - string, faculty/professor name or \"\" if not found\n"
    "  room        - string, room/lab number or \"\" if not found\n"
    "  start_time  - string, HH:MM 24-hour format (e.g. \"09:00\")\n"
    "  end_time    - string, HH:MM 24-hour format (e.g. \"10:00\")\n"
    "  class_type  - string, one of: Lecture Lab Tutorial Practical (default: Lecture)\n\n"
    "Rules:\n"
    "- Return ONLY a valid JSON array. No explanation, no markdown fences.\n"
    "- If a field is unknown, use an empty string \"\".\n"
    "- Convert 12-hour times (e.g. \"10:30 AM\") to 24-hour format.\n"
    "- If a slot spans multiple days, create one entry per day.\n"
    "- Skip holidays, lunch breaks, free periods."
)


async def parse_timetable_with_ai(raw_text: str) -> List[Dict[str, Any]]:
    """Send extracted text to Azure OpenAI; returns list of entry dicts."""
    if not (
        settings.AZURE_OPENAI_ENDPOINT
        and settings.AZURE_OPENAI_API_KEY
        and not settings.AZURE_OPENAI_API_KEY.startswith("your_")
    ):
        logger.warning("Azure OpenAI not configured -- cannot parse timetable structure.")
        return []

    try:
        from openai import AsyncAzureOpenAI

        client = AsyncAzureOpenAI(
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
            api_key=settings.AZURE_OPENAI_API_KEY,
            api_version=settings.AZURE_OPENAI_API_VERSION,
        )

        response = await client.chat.completions.create(
            model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": _PARSE_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Parse this timetable text and return ONLY a JSON array:\n\n"
                        + raw_text[:10000]
                    ),
                },
            ],
            temperature=0.0,
            max_tokens=3000,
        )

        content = (response.choices[0].message.content or "").strip()
        # Strip accidental markdown fences
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        entries: List[Dict[str, Any]] = json.loads(content)
        logger.info("Azure OpenAI parsed %d timetable entries.", len(entries))
        return entries

    except json.JSONDecodeError as exc:
        logger.error("Timetable AI response was not valid JSON: %s", exc)
        return []
    except Exception as exc:
        logger.error("Azure OpenAI timetable parsing failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Step 3: Orchestrator
# ---------------------------------------------------------------------------

async def parse_timetable_from_document(
    filename: str,
    file_bytes: bytes,
) -> Dict[str, Any]:
    """
    Full pipeline: file_bytes -> Document Intelligence (OCR) -> OpenAI (JSON).

    Returns:
        {
            "raw_text": str,
            "entries": [{"day", "subject", "code", "faculty", "room",
                         "start_time", "end_time", "class_type"}, ...],
            "warning": str | None,
        }
    """
    raw_text = await extract_text_from_document(filename, file_bytes)

    warning: Optional[str] = None

    if not raw_text.strip():
        return {
            "raw_text": "",
            "entries": [],
            "warning": "No text could be extracted from the uploaded file.",
        }

    entries = await parse_timetable_with_ai(raw_text)

    if not entries:
        warning = (
            "Azure OpenAI is not configured or could not parse the timetable. "
            "Please ensure AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY are set in .env."
        )

    # Validate / sanitise
    clean_entries = []
    for e in entries:
        day = str(e.get("day", "")).strip().capitalize()
        if day not in VALID_DAYS:
            continue
        clean_entries.append(
            {
                "day": day,
                "subject": str(e.get("subject", "Unknown Subject")).strip(),
                "code": str(e.get("code", "")).strip(),
                "faculty": str(e.get("faculty", "")).strip(),
                "room": str(e.get("room", "")).strip(),
                "start_time": str(e.get("start_time", "00:00")).strip() or "00:00",
                "end_time": str(e.get("end_time", "00:00")).strip() or "00:00",
                "class_type": str(e.get("class_type", "Lecture")).strip() or "Lecture",
            }
        )

    return {
        "raw_text": raw_text,
        "entries": clean_entries,
        "warning": warning,
    }
