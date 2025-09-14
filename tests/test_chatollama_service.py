import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from services.chatollama_service import (
    OllamaService,
    OllamaServiceError,
    OllamaConnectionError,
    OllamaTimeoutError,
    AsyncOllamaCallbackHandler,
    stream_blog_from_ollama
)


class TestAsyncOllamaCallbackHandler:
    """Test the AsyncOllamaCallbackHandler class"""
    
    @pytest.mark.asyncio
    async def test_callback_handler_initialization(self):
        """Test callback handler initialization"""
        handler = AsyncOllamaCallbackHandler()
        assert handler._done is False
        assert handler._queue is not None
    
    @pytest.mark.asyncio
    async def test_on_llm_new_token(self):
        """Test handling new tokens"""
        handler = AsyncOllamaCallbackHandler()
        await handler.on_llm_new_token("test token")
        
        # Check that token was added to queue
        item = await handler._queue.get()
        assert item["type"] == "token"
        assert item["content"] == "test token"
    
    @pytest.mark.asyncio
    async def test_on_llm_end(self):
        """Test handling LLM completion"""
        handler = AsyncOllamaCallbackHandler()
        response = MagicMock()
        await handler.on_llm_end(response)
        
        assert handler._done is True
        item = await handler._queue.get()
        assert item["type"] == "end"
        assert item["content"] == response
    
    @pytest.mark.asyncio
    async def test_on_llm_error(self):
        """Test handling LLM errors"""
        handler = AsyncOllamaCallbackHandler()
        error = Exception("Test error")
        await handler.on_llm_error(error)
        
        assert handler._done is True
        item = await handler._queue.get()
        assert item["type"] == "error"
        assert item["content"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_async_iterator(self):
        """Test async iteration over tokens"""
        handler = AsyncOllamaCallbackHandler()
        
        # Add some tokens
        await handler.on_llm_new_token("token1")
        await handler.on_llm_new_token("token2")
        await handler.on_llm_end(MagicMock())
        
        # Collect tokens
        tokens = []
        async for token in handler:
            tokens.append(token)
        
        assert tokens == ["token1", "token2"]


class TestOllamaService:
    """Test the OllamaService class"""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test"""
        return OllamaService()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization"""
        assert service._client is None
        assert service._connection_pool == {}
        assert service._last_request_time == 0
        assert service._request_count == 0
    
    @pytest.mark.asyncio
    async def test_validate_prompt_success(self, service):
        """Test successful prompt validation"""
        result = await service._validate_prompt("Valid prompt")
        assert result == "Valid prompt"
    
    @pytest.mark.asyncio
    async def test_validate_prompt_empty(self, service):
        """Test prompt validation with empty input"""
        with pytest.raises(ValueError, match="User prompt cannot be empty"):
            await service._validate_prompt("")
    
    @pytest.mark.asyncio
    async def test_validate_prompt_whitespace(self, service):
        """Test prompt validation with whitespace-only input"""
        with pytest.raises(ValueError, match="User prompt cannot be empty"):
            await service._validate_prompt("   ")
    
    @pytest.mark.asyncio
    async def test_validate_prompt_too_long(self, service):
        """Test prompt validation with overly long input"""
        long_prompt = "x" * 2001
        with pytest.raises(ValueError, match="User prompt too long"):
            await service._validate_prompt(long_prompt)
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self, service):
        """Test rate limiting functionality"""
        start_time = service._last_request_time
        
        await service._apply_rate_limiting()
        
        assert service._request_count == 1
        assert service._last_request_time > start_time
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_success(self, service):
        """Test retry with backoff on success"""
        mock_func = AsyncMock(return_value="success")
        
        result = await service._retry_with_backoff(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_failure_then_success(self, service):
        """Test retry with backoff that eventually succeeds"""
        mock_func = AsyncMock(side_effect=[Exception("fail"), Exception("fail"), "success"])
        
        result = await service._retry_with_backoff(mock_func)
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_with_backoff_all_failures(self, service):
        """Test retry with backoff when all attempts fail"""
        mock_func = AsyncMock(side_effect=Exception("fail"))
        
        with pytest.raises(Exception, match="fail"):
            await service._retry_with_backoff(mock_func)
        
        assert mock_func.call_count == 3  # Default max retries
    
    @pytest.mark.asyncio
    async def test_request_context(self, service):
        """Test request context manager"""
        async with service._request_context("test prompt") as request_id:
            assert request_id.startswith("req_")
            assert service._request_count == 1
    
    @pytest.mark.asyncio
    async def test_request_context_error_handling(self, service):
        """Test request context error handling"""
        with pytest.raises(ValueError):
            async with service._request_context(""):
                pass
    
    @pytest.mark.asyncio
    async def test_get_client_creates_new_connection(self, service):
        """Test creating new client connection"""
        with patch('services.chatollama_service.Ollama') as mock_ollama:
            mock_ollama.return_value = MagicMock()
            
            client = await service._get_client("test-model")
            
            assert client is not None
            mock_ollama.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_connection(self, service):
        """Test reusing existing client connection"""
        with patch('services.chatollama_service.Ollama') as mock_ollama:
            mock_ollama.return_value = MagicMock()
            
            # Create first client
            client1 = await service._get_client("test-model")
            # Get second client
            client2 = await service._get_client("test-model")
            
            assert client1 is client2
            assert mock_ollama.call_count == 1  # Only called once
    
    @pytest.mark.asyncio
    async def test_stream_blog_content_invalid_format(self, service):
        """Test streaming with invalid output format"""
        with pytest.raises(ValueError, match="Unsupported output format"):
            async for _ in service.stream_blog_content("test", "invalid"):
                pass
    
    @pytest.mark.asyncio
    async def test_stream_blog_content_success(self, service):
        """Test successful blog content streaming"""
        with patch.object(service, '_get_client') as mock_get_client, \
             patch.object(service, '_validate_prompt') as mock_validate:
            
            mock_validate.return_value = "validated prompt"
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            # Mock the agenerate method
            mock_client.agenerate = AsyncMock(return_value=MagicMock())
            
            # Mock the callback handler
            with patch('services.chatollama_service.AsyncOllamaCallbackHandler') as mock_handler_class:
                mock_handler = MagicMock()
                mock_handler_class.return_value = mock_handler
                mock_handler.__aiter__ = AsyncMock(return_value=iter(["token1", "token2"]))
                
                tokens = []
                async for token in service.stream_blog_content("test prompt"):
                    tokens.append(token)
                
                assert tokens == ["token1", "token2"]
    
    @pytest.mark.asyncio
    async def test_generate_blog_content(self, service):
        """Test non-streaming blog content generation"""
        with patch.object(service, 'stream_blog_content') as mock_stream:
            mock_stream.return_value = iter(["part1", "part2", "part3"])
            
            result = await service.generate_blog_content("test prompt")
            
            assert result == "part1part2part3"
    
    @pytest.mark.asyncio
    async def test_get_model_info(self, service):
        """Test getting model information"""
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            info = await service.get_model_info("test-model")
            
            assert info["model"] == "test-model"
            assert info["status"] == "connected"
    
    @pytest.mark.asyncio
    async def test_close(self, service):
        """Test closing the service"""
        # Add some mock connections
        service._connection_pool = {"test": MagicMock()}
        
        await service.close()
        
        assert service._connection_pool == {}


class TestBackwardCompatibility:
    """Test backward compatibility functions"""
    
    @pytest.mark.asyncio
    async def test_stream_blog_from_ollama(self):
        """Test the backward compatibility function"""
        with patch('services.chatollama_service.ollama_service') as mock_service:
            mock_service.stream_blog_content.return_value = iter(["token1", "token2"])
            
            tokens = []
            async for token in stream_blog_from_ollama("test prompt"):
                tokens.append(token)
            
            assert tokens == ["token1", "token2"]
            mock_service.stream_blog_content.assert_called_once_with("test prompt", "html")


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection errors"""
        service = OllamaService()
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Connection refused")
            
            with pytest.raises(OllamaConnectionError, match="Failed to connect to Ollama"):
                await service._get_client("test-model")
    
    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors"""
        service = OllamaService()
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.agenerate = AsyncMock(side_effect=asyncio.TimeoutError())
            
            with pytest.raises(OllamaTimeoutError):
                async for _ in service.stream_blog_content("test prompt"):
                    pass
    
    @pytest.mark.asyncio
    async def test_generic_service_error(self):
        """Test handling of generic service errors"""
        service = OllamaService()
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            mock_client.agenerate = AsyncMock(side_effect=Exception("Unknown error"))
            
            with pytest.raises(OllamaServiceError, match="Unexpected error"):
                async for _ in service.stream_blog_content("test prompt"):
                    pass


if __name__ == "__main__":
    pytest.main([__file__])


