from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class BlogResponse(BaseModel):
    topic: str
    blog_html: str
    image_url: Optional[str] = None
    image_description: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    style: str = "professional"

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0.0"
    services: Dict[str, str] = Field(default_factory=dict)

class WebSocketResponse(BaseModel):
    type: str  # "blog", "image", "error", "complete"
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow) 