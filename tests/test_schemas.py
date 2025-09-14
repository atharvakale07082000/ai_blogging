import pytest
from pydantic import ValidationError
from schemas.requests import BlogRequest, WebSocketMessage

def test_valid_blog_request():
    """Test valid blog request"""
    request = BlogRequest(topic="Test Blog Topic")
    assert request.topic == "Test Blog Topic"
    assert request.include_image is True
    assert request.style == "professional"

def test_invalid_blog_request():
    """Test invalid blog request"""
    with pytest.raises(ValidationError):
        BlogRequest(topic="")  # Empty topic
    
    with pytest.raises(ValidationError):
        BlogRequest(topic="   ")  # Whitespace only

def test_valid_websocket_message():
    """Test valid WebSocket message"""
    message = WebSocketMessage(topic="Test Topic")
    assert message.topic == "Test Topic"
    assert message.include_image is True
    assert message.style == "professional"

def test_blog_request_with_custom_values():
    """Test blog request with custom values"""
    request = BlogRequest(
        topic="Custom Topic",
        include_image=False,
        style="casual"
    )
    assert request.topic == "Custom Topic"
    assert request.include_image is False
    assert request.style == "casual"

def test_topic_trimming():
    """Test that topics are properly trimmed"""
    request = BlogRequest(topic="  Test Topic  ")
    assert request.topic == "Test Topic" 