from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[dict] = None

class ChatSession(BaseModel):
    id: Optional[str] = None
    topic: str
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "active"  # "active", "completed", "failed"
    blog_html: Optional[str] = None
    image_url: Optional[str] = None
    image_description: Optional[str] = None
    style: str = "professional"
    
    def add_message(self, role: str, content: str, metadata: Optional[dict] = None):
        """Add a new message to the chat session"""
        message = ChatMessage(
            role=role,
            content=content,
            metadata=metadata
        )
        self.messages.append(message)
        self.updated_at = datetime.utcnow()
        return message
    
    def get_messages_by_role(self, role: str) -> List[ChatMessage]:
        """Get all messages by a specific role"""
        return [msg for msg in self.messages if msg.role == role]
    
    def get_last_message(self) -> Optional[ChatMessage]:
        """Get the last message in the session"""
        return self.messages[-1] if self.messages else None
