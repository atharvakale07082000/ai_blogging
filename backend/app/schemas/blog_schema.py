from pydantic import BaseModel, Field
from typing import Optional, List

class BlogGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=3, description="Main topic of the blog post")
    tone: str = Field(default="informative", description="Tone of the blog (e.g., professional, casual, humorous)")
    keywords: List[str] = Field(default=[], description="List of keywords to include")
    length: str = Field(default="medium", description="Desired length (short, medium, long)")
    target_audience: str = Field(default="general", description="Target audience for the blog")

class BlogResponse(BaseModel):
    title: str
    outline: List[str]
    content: str
    seo_metadata: dict
