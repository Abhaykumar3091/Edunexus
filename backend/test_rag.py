import asyncio
from app.services.blob_qa_service import load_all_blobs, search_blobs_for_answer, _get_relevant_chunks
from app.services.azure_openai import _retrieve_rag_context

async def test():
    blobs = await load_all_blobs()
    print("Blobs in cache:", list(blobs.keys()))
    hostel_text = blobs.get("Hostel-Rules-2023-24.pdf", "")
    print("Hostel text len:", len(hostel_text))
    
    # search for keywords in hostel text
    for word in ["item", "allow", "prohibit", "belonging", "appliance", "possession", "room", "electric"]:
        cnt = hostel_text.lower().count(word)
        print(f"Count of '{word}':", cnt)
        
    print("\n=== Testing search_blobs_for_answer for 'Allowed items in hostel?' ===")
    blob_srcs = await search_blobs_for_answer("Allowed items in hostel?")
    for s in blob_srcs:
        print("--- Doc:", s.document_title, "Score:", s.relevance_score)
        print(s.chunk_text[:300])
        
    print("\n=== Testing full _retrieve_rag_context ===")
    context, sources = await _retrieve_rag_context("Allowed items in hostel?")
    print("Context length:", len(context))
    print("Context snippet:\n", context[:1500])

asyncio.run(test())
