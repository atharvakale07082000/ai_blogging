import autogen
import asyncio
import logging
from typing import Tuple, Optional, Dict, Any
from config import settings
from tools.image_tools import generate_image_from_description
from schemas.responses import WebSocketResponse
from models.chat import ChatSession

logger = logging.getLogger(__name__)

# Define LLM config using settings - now using Gemini 2.5 Flash
llm_config = {
    "config_list": [
        {
            "model": settings.LLM_MODEL,
            "api_key": settings.LLM_API_KEY,
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai" if settings.LLM_PROVIDER.lower() == "gemini" else settings.OPENAI_BASE_URL
        }
    ],
    "model": settings.LLM_MODEL
}

# User proxy agent (initiates the task and collects results)
user_proxy = autogen.UserProxyAgent(
    name="User",
    llm_config=llm_config,
    system_message="You are the user who wants a blog and an image for a given topic. Collect the results from the agents and present them together.",
    human_input_mode="NEVER"
)

# Blog generation agent
blog_agent = autogen.AssistantAgent(
    name="BlogWriter",
    llm_config=llm_config,
    system_message="You are a professional blog writer. Write a detailed, engaging blog post in HTML format about the given topic. Use headings, paragraphs, and lists as appropriate."
)

# Image generation agent
image_agent = autogen.AssistantAgent(
    name="ImageGenerator",
    llm_config=llm_config,
    system_message="You are an AI that generates a description for an image suitable for a blog post about the given topic. Output a short, vivid description that could be used to generate an image with an AI image generator. If you are asked to generate an image, call the 'generate_image_from_description' tool with the description you create."
)

# Register the image generation tool with the image agent
image_agent.register_for_llm(name="generate_image_from_description", description="Generate an image from a description.")(generate_image_from_description)

def _make_groupchat(topic: str, style: str = "professional"):
    # Each agent gets a specific instruction with style
    blog_msg = f"Write a {style} blog about: {topic}. Use HTML formatting with proper tags."
    image_msg = f"Generate an image description for a {style} blog about: {topic}"
    
    groupchat = autogen.GroupChat(
        agents=[user_proxy, blog_agent, image_agent],
        messages=[
            {"role": "user", "content": blog_msg, "recipient": "BlogWriter"},
            {"role": "user", "content": image_msg, "recipient": "ImageGenerator"}
        ],
        max_round=2
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)
    return groupchat, manager

async def generate_blog_and_image(
    topic: str, 
    stream: bool = False, 
    websocket = None,
    style: str = "professional"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Advanced workflow: UserProxyAgent initiates a group chat with BlogWriter and ImageGenerator.
    Both agents work in parallel, coordinated by GroupChatManager.
    
    Args:
        topic: The blog topic
        stream: Whether to stream results via WebSocket
        websocket: WebSocket connection for streaming
        style: Writing style for the blog
    
    Returns:
        Tuple of (blog_html, image_desc)
    """
    try:
        logger.info(f"Starting blog generation for topic: {topic}")
        
        # Create chat session for tracking
        chat_session = ChatSession(topic=topic, style=style)
        
        loop = asyncio.get_event_loop()
        groupchat, manager = _make_groupchat(topic, style)
        
        # Run the group chat in a thread to avoid blocking
        def run_chat():
            try:
                return user_proxy.initiate_chat(manager)
            except Exception as e:
                logger.error(f"Error in group chat: {e}")
                raise
        
        result = await loop.run_in_executor(None, run_chat)
        
        # Parse results from the group chat messages
        blog_html = None
        image_desc = None
        
        for msg in groupchat.messages:
            if msg.get("role") == "assistant" and msg.get("sender") == "BlogWriter":
                blog_html = msg.get("content")
                if stream and websocket:
                    response = WebSocketResponse(
                        type="blog",
                        data={"blog_html": blog_html}
                    )
                    await websocket.send_json(response.dict())
                    
            if msg.get("role") == "assistant" and msg.get("sender") == "ImageGenerator":
                image_desc = msg.get("content")
                if stream and websocket:
                    response = WebSocketResponse(
                        type="image",
                        data={"image_description": image_desc}
                    )
                    await websocket.send_json(response.dict())
        
        # Update chat session
        chat_session.blog_html = blog_html
        chat_session.image_description = image_desc
        chat_session.status = "completed"
        
        logger.info(f"Blog generation completed for topic: {topic}")
        return blog_html, image_desc
        
    except Exception as e:
        logger.error(f"Error generating blog for topic '{topic}': {e}")
        if stream and websocket:
            error_response = WebSocketResponse(
                type="error",
                data={"error": str(e)}
            )
            await websocket.send_json(error_response.dict())
        raise 