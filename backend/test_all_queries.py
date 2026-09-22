import asyncio
from app.services.azure_openai import get_ai_response
from app.services.blob_qa_service import load_all_blobs

async def main():
    print("=== Initializing Knowledge Base ===")
    await load_all_blobs(force=True)

    test_queries = [
        "Allowed items in hostel?",
        "Can I bring an electric kettle or heater to my hostel room?",
        "What are the hostel silence hours?",
        "What is the fee structure for MBA in Marketing for 2026?",
        "What is the attendance requirement and passing marks in exams?",
    ]

    for q in test_queries:
        print(f"\n==========================================")
        print(f"QUERY: {q}")
        print(f"==========================================")
        resp = await get_ai_response(q, [])
        print("ANSWER:\n" + resp["answer"])
        print("\nSOURCES:")
        for s in resp.get("sources", []):
            print(f" - {s.get('title') or s.get('document_title')}: {s.get('section')}")

asyncio.run(main())
