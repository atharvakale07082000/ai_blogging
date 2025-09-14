import logging
import time
import json
from datetime import datetime
from typing import Dict, Any
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from config import settings

# Configure structured logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format=settings.LOG_FORMAT
)

class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.logger = logging.getLogger("api")
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract request details
        request_data = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Log request
        self.logger.info("Request started", extra={"request": request_data})
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            response_data = {
                "status_code": response.status_code,
                "process_time": round(process_time, 4),
                "content_length": len(response.body) if hasattr(response, 'body') else 0
            }
            
            self.logger.info(
                "Request completed",
                extra={
                    "request": request_data,
                    "response": response_data
                }
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Log error
            error_data = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "process_time": time.time() - start_time
            }
            
            self.logger.error(
                "Request failed",
                extra={
                    "request": request_data,
                    "error": error_data
                },
                exc_info=True
            )
            raise
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

class WebSocketLoggingMiddleware:
    """Middleware for logging WebSocket connections"""
    
    def __init__(self):
        self.logger = logging.getLogger("websocket")
    
    async def log_websocket_connection(self, websocket, client_ip: str):
        """Log WebSocket connection"""
        self.logger.info(
            "WebSocket connected",
            extra={
                "client_ip": client_ip,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def log_websocket_message(self, websocket, message: str, client_ip: str):
        """Log WebSocket message"""
        self.logger.info(
            "WebSocket message received",
            extra={
                "client_ip": client_ip,
                "message_length": len(message),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    async def log_websocket_disconnect(self, websocket, client_ip: str):
        """Log WebSocket disconnection"""
        self.logger.info(
            "WebSocket disconnected",
            extra={
                "client_ip": client_ip,
                "timestamp": datetime.utcnow().isoformat()
            }
        ) 