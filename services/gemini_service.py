import asyncio
import logging
import time
from typing import AsyncGenerator, Dict, Any, Optional, Union
from contextlib import asynccontextmanager

import google.generativeai as genai
from google.generativeai.types import GenerateContentResponse

from config import settings
import structlog

# Configure structured logging
logger = structlog.get_logger(__name__)

# Prompt templates for different content types
PROMPT_TEMPLATES = {
    "html": """
You are a helpful AI assistant that writes blog content. Respond to the following prompt as a well-structured HTML5 article, using appropriate tags (such as <h1>, <h2>, <p>, <ul>, <li>, <strong>, <em>, etc). Do not include markdown or plain text, only valid HTML. The content should be ready to render in a browser.

Prompt: {user_prompt}
""",
    "markdown": """
You are a helpful AI assistant that writes blog content. Respond to the following prompt as a well-structured Markdown article with proper headings, paragraphs, lists, and formatting.

Prompt: {user_prompt}
""",
    "plain": """
You are a helpful AI assistant that writes blog content. Respond to the following prompt as a well-structured article with clear sections and formatting.

Prompt: {user_prompt}
"""
}

class GeminiServiceError(Exception):
    """Custom exception for Gemini service errors"""
    pass

class GeminiConnectionError(GeminiServiceError):
    """Exception raised when connection to Gemini fails"""
    pass

class GeminiTimeoutError(GeminiServiceError):
    """Exception raised when Gemini request times out"""
    pass

class GeminiService:
    """Service class for interacting with Google Gemini 2.5 Flash models"""
    
    def __init__(self):
        self._client: Optional[genai.GenerativeModel] = None
        self._connection_pool: Dict[str, genai.GenerativeModel] = {}
        self._last_request_time = 0
        self._request_count = 0
        self._initialized = False
    
    async def _initialize_client(self):
        """Initialize Gemini client with API key"""
        if not self._initialized:
            try:
                if not settings.GEMINI_API_KEY:
                    raise GeminiConnectionError("GEMINI_API_KEY not found in configuration")
                
                genai.configure(api_key=settings.GEMINI_API_KEY)
                self._initialized = True
                logger.info("Gemini client initialized successfully")
            except Exception as e:
                logger.error("Failed to initialize Gemini client", error=str(e))
                raise GeminiConnectionError(f"Failed to initialize Gemini: {e}")
    
    async def _get_client(self, model: Optional[str] = None) -> genai.GenerativeModel:
        """Get or create Gemini client with connection pooling"""
        await self._initialize_client()
        
        model = model or settings.GEMINI_MODEL
        model_key = f"gemini_{model}"
        
        if model_key not in self._connection_pool:
            try:
                client = genai.GenerativeModel(
                    model_name=model,
                    generation_config={
                        "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
                        "temperature": settings.GEMINI_TEMPERATURE,
                        "top_p": settings.GEMINI_TOP_P,
                        "top_k": settings.GEMINI_TOP_K,
                    }
                )
                self._connection_pool[model_key] = client
                logger.info("Created new Gemini client", model=model)
            except Exception as e:
                logger.error("Failed to create Gemini client", error=str(e), model=model)
                raise GeminiConnectionError(f"Failed to connect to Gemini: {e}")
        
        return self._connection_pool[model_key]
    
    async def _validate_prompt(self, user_prompt: str) -> str:
        """Validate and sanitize user prompt"""
        if not user_prompt or not user_prompt.strip():
            raise ValueError("User prompt cannot be empty")
        
        # Basic sanitization - remove potentially harmful content
        sanitized = user_prompt.strip()
        if len(sanitized) > 2000:  # Reasonable limit for blog prompts
            raise ValueError("User prompt too long (max 2000 characters)")
        
        return sanitized
    
    async def _apply_rate_limiting(self):
        """Apply rate limiting to prevent abuse"""
        current_time = time.time()
        if current_time - self._last_request_time < 60.0 / settings.RATE_LIMIT_PER_MINUTE:
            await asyncio.sleep(0.1)  # Small delay
        self._last_request_time = current_time
        self._request_count += 1
    
    async def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry function with exponential backoff"""
        last_exception = None
        
        for attempt in range(3):  # Default retry count
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < 2:  # 3 attempts total
                    delay = 1.0 * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        "Gemini request failed, retrying",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Gemini request failed after all retries", error=str(e))
                    raise last_exception
    
    @asynccontextmanager
    async def _request_context(self, user_prompt: str, model: Optional[str] = None):
        """Context manager for Gemini requests with proper cleanup"""
        start_time = time.time()
        request_id = f"req_{int(start_time * 1000)}"
        
        logger.info(
            "Starting Gemini request",
            request_id=request_id,
            model=model or settings.GEMINI_MODEL,
            prompt_length=len(user_prompt)
        )
        
        try:
            await self._apply_rate_limiting()
            yield request_id
        except Exception as e:
            logger.error(
                "Gemini request failed",
                request_id=request_id,
                error=str(e),
                duration=time.time() - start_time
            )
            raise
        finally:
            logger.info(
                "Gemini request completed",
                request_id=request_id,
                duration=time.time() - start_time
            )
    
    async def stream_blog_content(
        self,
        user_prompt: str,
        output_format: str = "html",
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Stream blog content from Gemini 2.5 Flash with comprehensive error handling and monitoring.
        
        Args:
            user_prompt: The user's prompt for blog content
            output_format: Output format ('html', 'markdown', 'plain')
            model: Specific Gemini model to use
            **kwargs: Additional parameters for the LLM
        
        Yields:
            Streaming content chunks
            
        Raises:
            GeminiServiceError: For service-related errors
            ValueError: For invalid input parameters
        """
        # Validate input parameters
        if output_format not in PROMPT_TEMPLATES:
            raise ValueError(f"Unsupported output format: {output_format}. Supported: {list(PROMPT_TEMPLATES.keys())}")
        
        sanitized_prompt = await self._validate_prompt(user_prompt)
        
        async with self._request_context(sanitized_prompt, model) as request_id:
            try:
                # Get Gemini client
                client = await self._get_client(model)
                
                # Create formatted prompt
                formatted_prompt = PROMPT_TEMPLATES[output_format].format(user_prompt=sanitized_prompt)
                
                # Execute with retry logic
                async def execute_stream():
                    return await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: client.generate_content(formatted_prompt, stream=True)
                    )
                
                # Get streaming response
                response_stream = await self._retry_with_backoff(execute_stream)
                
                # Stream tokens
                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                
            except asyncio.TimeoutError:
                raise GeminiTimeoutError("Request timed out")
            except Exception as e:
                if "connection" in str(e).lower() or "api" in str(e).lower():
                    raise GeminiConnectionError(f"Connection to Gemini failed: {e}")
                else:
                    raise GeminiServiceError(f"Unexpected error: {e}")
    
    async def generate_blog_content(
        self,
        user_prompt: str,
        output_format: str = "html",
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate complete blog content (non-streaming) from Gemini 2.5 Flash.
        
        Args:
            user_prompt: The user's prompt for blog content
            output_format: Output format ('html', 'markdown', 'plain')
            model: Specific Gemini model to use
            **kwargs: Additional parameters for the LLM
        
        Returns:
            Complete blog content as string
        """
        content_parts = []
        async for chunk in self.stream_blog_content(user_prompt, output_format, model, **kwargs):
            content_parts.append(chunk)
        
        return "".join(content_parts)
    
    async def get_model_info(self, model: Optional[str] = None) -> Dict[str, Any]:
        """Get information about available Gemini models"""
        try:
            await self._initialize_client()
            model = model or settings.GEMINI_MODEL
            return {
                "model": model,
                "provider": "google_gemini",
                "status": "connected",
                "max_output_tokens": settings.GEMINI_MAX_OUTPUT_TOKENS,
                "temperature": settings.GEMINI_TEMPERATURE,
                "top_p": settings.GEMINI_TOP_P,
                "top_k": settings.GEMINI_TOP_K
            }
        except Exception as e:
            logger.error("Failed to get model info", error=str(e))
            raise GeminiServiceError(f"Failed to get model info: {e}")
    
    async def close(self):
        """Clean up resources and close connections"""
        self._connection_pool.clear()
        logger.info("Gemini service connections closed")

# Global service instance
gemini_service = GeminiService()

# Backward compatibility function
async def stream_blog_from_gemini(user_prompt: str) -> AsyncGenerator[str, None]:
    """
    Backward compatibility function for streaming blog content.
    Use GeminiService.stream_blog_content() for new implementations.
    """
    async for chunk in gemini_service.stream_blog_content(user_prompt, "html"):
        yield chunk
