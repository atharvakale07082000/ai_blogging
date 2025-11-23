import google.generativeai as genai
from app.core.config import settings
from app.schemas.blog_schema import BlogGenerationRequest, BlogResponse
import json
import logging

logger = logging.getLogger(__name__)

class AIBlogService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.MODEL_NAME)

    async def generate_blog(self, request: BlogGenerationRequest) -> BlogResponse:
        prompt = self._create_prompt(request)
        
        try:
            response = self.model.generate_content(prompt)
            # Gemini response might need parsing if we ask for JSON specifically
            # For robustness, we'll ask for a structured JSON response in the prompt
            
            content_text = response.text
            # Clean up potential markdown code blocks if Gemini wraps in ```json ... ```
            if content_text.startswith("```json"):
                content_text = content_text.replace("```json", "").replace("```", "")
            elif content_text.startswith("```"):
                content_text = content_text.replace("```", "")
            
            data = json.loads(content_text)
            
            return BlogResponse(
                title=data.get("title", "Untitled"),
                outline=data.get("outline", []),
                content=data.get("content", ""),
                seo_metadata=data.get("seo_metadata", {})
            )
        except Exception as e:
            logger.error(f"Error generating blog: {str(e)}")
            raise e

    def _create_prompt(self, request: BlogGenerationRequest) -> str:
        return f"""
        Act as an expert SEO content writer. Generate a blog post based on the following parameters:
        
        Topic: {request.topic}
        Tone: {request.tone}
        Keywords: {", ".join(request.keywords)}
        Length: {request.length}
        Target Audience: {request.target_audience}
        
        Output the result STRICTLY as a valid JSON object with the following structure:
        {{
            "title": "Catchy and SEO-optimized title",
            "outline": ["Section 1", "Section 2", ...],
            "content": "The full blog post content in Markdown format",
            "seo_metadata": {{
                "meta_description": "160 char description",
                "tags": ["tag1", "tag2"]
            }}
        }}
        """

ai_blog_service = AIBlogService()
