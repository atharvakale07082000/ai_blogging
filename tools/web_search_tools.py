import os
import logging
from typing import Optional
from config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)


def web_search(query: str) -> str:
    """
    Uses OpenAI API to simulate web search (retrieval-augmented generation).
    In production, use a real web search API or RAG pipeline.
    
    Args:
        query: Search query string
        
    Returns:
        Search results as string
        
    Raises:
        Exception: If search fails
    """
    try:
        if not query or not query.strip():
            raise ValueError("Search query cannot be empty")
        
        if not settings.LLM_API_KEY:
            raise ValueError("LLM API key not configured")

        # Create OpenAI-compatible client (works for OpenAI and Gemini Responses API)
        client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL
        )
        
        logger.info(f"Performing web search for query: {query}")
        
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions using up-to-date web information. If you don't know, say so."},
                {"role": "user", "content": f"Search the web and summarize the latest information about: {query}"}
            ],
            max_tokens=256,
            temperature=0.2
        )
        content = response.choices[0].message.content if response.choices and hasattr(response.choices[0].message, "content") else None
        result = content.strip() if content else "[No content returned from LLM API.]"
        
        logger.info(f"Web search completed for query: {query}")
        return result
        
    except Exception as e:
        logger.error(f"Web search failed for query '{query}': {e}")
        raise Exception(f"Web search failed: {str(e)}")

def validate_search_query(query: str) -> bool:
    """
    Validate search query for appropriateness and length.
    
    Args:
        query: The search query to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not query or not query.strip():
        return False
    
    if len(query) > 200:
        return False
    
    # Add more validation as needed (content filtering, etc.)
    return True 