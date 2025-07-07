import httpx
import asyncio

OLLAMA_API_URL = "http://localhost:11434/api/chat"

async def stream_blog_from_ollama(prompt: str):
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST", OLLAMA_API_URL, json={"prompt": prompt, "stream": True}
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    yield line 