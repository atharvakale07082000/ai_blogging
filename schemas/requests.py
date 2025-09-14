from pydantic import BaseModel, Field, validator
from typing import Optional

class BlogRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500, description="The topic for the blog post")
    include_image: bool = Field(default=True, description="Whether to generate an image")
    style: Optional[str] = Field(default="professional", description="Writing style for the blog")
    
    @validator('topic')
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError("Topic cannot be empty or whitespace")
        return v.strip()

class WebSocketMessage(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    include_image: bool = Field(default=True)
    style: Optional[str] = Field(default="professional")
    
    @validator('topic')
    def validate_topic(cls, v):
        if not v.strip():
            raise ValueError("Topic cannot be empty or whitespace")
        return v.strip() 