from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.responses import JSONResponse
from services.autogen_agents import generate_blog_and_image
from schemas.requests import WebSocketMessage, BlogRequest
from schemas.responses import BlogResponse, ErrorResponse, HealthResponse, WebSocketResponse
from middleware.logging import WebSocketLoggingMiddleware
import asyncio
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)
ws_logger = WebSocketLoggingMiddleware()

router = APIRouter()

async def stream_blog_and_image(topic: str, websocket: WebSocket, style: str = "professional"):
    """Stream blog and image generation results via WebSocket"""
    try:
        await generate_blog_and_image(
            topic=topic, 
            stream=True, 
            websocket=websocket,
            style=style
        )
        
        # Send completion message
        completion_response = WebSocketResponse(
            type="complete",
            data={"message": "Blog generation completed"}
        )
        await websocket.send_json(completion_response.dict())
        
    except Exception as e:
        logger.error(f"Error in stream_blog_and_image: {e}")
        error_response = WebSocketResponse(
            type="error",
            data={"error": str(e)}
        )
        await websocket.send_json(error_response.dict())

@router.websocket("/ws/agent-blog")
async def websocket_agent_blog(websocket: WebSocket):
    """WebSocket endpoint for streaming blog generation"""
    client_ip = websocket.client.host if websocket.client else "unknown"
    
    await websocket.accept()
    await ws_logger.log_websocket_connection(websocket, client_ip)
    
    try:
        # Receive and validate message
        data = await websocket.receive_json()
        await ws_logger.log_websocket_message(websocket, str(data), client_ip)
        
        # Validate input using Pydantic
        try:
            message = WebSocketMessage(**data)
        except Exception as validation_error:
            error_response = WebSocketResponse(
                type="error",
                data={"error": f"Invalid input: {str(validation_error)}"}
            )
            await websocket.send_json(error_response.dict())
            await websocket.close()
            return
        
        # Stream the results as they are generated
        await stream_blog_and_image(
            topic=message.topic,
            websocket=websocket,
            style=message.style
        )
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_ip}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            error_response = WebSocketResponse(
                type="error",
                data={"error": str(e)}
            )
            await websocket.send_json(error_response.dict())
        except:
            pass
    finally:
        await ws_logger.log_websocket_disconnect(websocket, client_ip)

@router.post("/blog", response_model=BlogResponse)
async def generate_blog_sync(request: BlogRequest):
    """Synchronous endpoint for blog generation"""
    try:
        blog_html, image_desc = await generate_blog_and_image(
            topic=request.topic,
            style=request.style
        )
        
        return BlogResponse(
            topic=request.topic,
            blog_html=blog_html or "",
            image_description=image_desc,
            style=request.style
        )
        
    except Exception as e:
        logger.error(f"Error generating blog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        services={
            "autogen": "healthy",
            "websocket": "healthy"
        }
    ) 