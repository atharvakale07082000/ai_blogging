import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

def generate_image_from_description(description: str) -> str:
    """
    Generate an image from a description.
    
    Args:
        description: Text description of the image to generate
        
    Returns:
        URL or path to the generated image
        
    Raises:
        Exception: If image generation fails
    """
    try:
        if not description or not description.strip():
            raise ValueError("Image description cannot be empty")
        
        # Sanitize description for URL
        sanitized_desc = description.replace(' ', '+')[:50]
        
        # In production, this would call a real image generation API
        # For now, return a placeholder
        if settings.IMAGE_GENERATION_ENABLED:
            image_url = f"https://dummyimage.com/600x400/000/fff&text={sanitized_desc}"
            logger.info(f"Generated image URL: {image_url}")
            return image_url
        else:
            logger.warning("Image generation is disabled")
            return ""
            
    except Exception as e:
        logger.error(f"Error generating image from description '{description}': {e}")
        raise Exception(f"Image generation failed: {str(e)}")

def validate_image_description(description: str) -> bool:
    """
    Validate image description for appropriateness and length.
    
    Args:
        description: The image description to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not description or not description.strip():
        return False
    
    if len(description) > 500:
        return False
    
    # Add more validation as needed (content filtering, etc.)
    return True 