from fastapi import APIRouter, HTTPException, Depends
from app.schemas.blog_schema import BlogGenerationRequest, BlogResponse
from app.services.ai_blog_service import ai_blog_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate-blog", response_model=BlogResponse)
async def generate_blog(request: BlogGenerationRequest):
    try:
        logger.info(f"Generating blog for topic: {request.topic}")
        blog = await ai_blog_service.generate_blog(request)
        return blog
    except Exception as e:
        logger.error(f"Failed to generate blog: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate blog: {str(e)}")
