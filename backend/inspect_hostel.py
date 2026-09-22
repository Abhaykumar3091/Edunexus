import asyncio
from app.services.blob_qa_service import load_all_blobs

async def inspect():
    blobs = await load_all_blobs()
    text = blobs.get("Hostel-Rules-2023-24.pdf", "")
    with open("hostel_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Hostel text saved! Total length:", len(text))

asyncio.run(inspect())
