import time
import asyncio
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from config import settings

logger = logging.getLogger(__name__)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.requests = defaultdict(list)
        self._cleanup_task = None
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if not self._is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {self.requests_per_minute} requests per minute."
            )
        
        # Record the request
        self._record_request(client_ip)
        
        # Process the request
        response = await call_next(request)
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _is_allowed(self, client_ip: str) -> bool:
        """Check if the client is within rate limits"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if req_time > minute_ago
        ]
        
        return len(self.requests[client_ip]) < self.requests_per_minute
    
    def _record_request(self, client_ip: str):
        """Record a request for the client"""
        self.requests[client_ip].append(time.time())
    
    async def _cleanup_old_requests(self):
        """Periodically clean up old request records"""
        while True:
            await asyncio.sleep(60)  # Clean up every minute
            now = time.time()
            minute_ago = now - 60
            
            for client_ip in list(self.requests.keys()):
                self.requests[client_ip] = [
                    req_time for req_time in self.requests[client_ip] 
                    if req_time > minute_ago
                ]
                # Remove empty entries
                if not self.requests[client_ip]:
                    del self.requests[client_ip] 