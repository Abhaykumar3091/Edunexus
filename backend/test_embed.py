import asyncio
from openai import AsyncAzureOpenAI
from app.core.config import settings

async def test_embed():
    client = AsyncAzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )
    res = await client.embeddings.create(
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=["Allowed items in hostel?", "Electrical equipment inside hostel rooms"]
    )
    print("Embedding vectors received! Dim:", len(res.data[0].embedding))

asyncio.run(test_embed())
