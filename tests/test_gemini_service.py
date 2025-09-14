import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from services.gemini_service import (
    GeminiService,
    GeminiServiceError,
    GeminiConnectionError,
    GeminiTimeoutError,
    stream_blog_from_gemini
)


class TestGeminiService:
    """Test the GeminiService class"""
    
    @pytest.fixture
    def service(self):
        """Create a fresh service instance for each test"""
        return GeminiService()
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, service):
        """Test service initialization"""
        assert service._client is None
        assert service._connection_pool == {}
        assert service._last_request_time == 0
        assert service._request_count == 0
        assert service._initialized is False
    
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
    async def test_initialize_client_success(self, service):
        """Test successful client initialization"""
        with patch('services.gemini_service.genai') as mock_genai, \
             patch('services.gemini_service.settings') as mock_settings:
            
            mock_settings.GEMINI_API_KEY = "test_api_key"
            
            await service._initialize_client()
            
            assert service._initialized is True
            mock_genai.configure.assert_called_once_with(api_key="test_api_key")
    
    @pytest.mark.asyncio
    async def test_initialize_client_no_api_key(self, service):
        """Test client initialization without API key"""
        with patch('services.gemini_service.settings') as mock_settings:
            mock_settings.GEMINI_API_KEY = None
            
            with pytest.raises(GeminiConnectionError, match="GEMINI_API_KEY not found"):
                await service._initialize_client()
    
    @pytest.mark.asyncio
    async def test_get_client_creates_new_connection(self, service):
        """Test creating new client connection"""
        with patch.object(service, '_initialize_client') as mock_init, \
             patch('services.gemini_service.genai.GenerativeModel') as mock_model:
            
            mock_client = MagicMock()
            mock_model.return_value = mock_client
            
            client = await service._get_client("test-model")
            
            assert client is not None
            mock_model.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_client_reuses_existing_connection(self, service):
        """Test reusing existing client connection"""
        with patch.object(service, '_initialize_client') as mock_init, \
             patch('services.gemini_service.genai.GenerativeModel') as mock_model:
            
            mock_client = MagicMock()
            mock_model.return_value = mock_client
            
            # Create first client
            client1 = await service._get_client("test-model")
            # Get second client
            client2 = await service._get_client("test-model")
            
            assert client1 is client2
            assert mock_model.call_count == 1  # Only called once
    
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
            
            # Mock the generate_content method with streaming
            mock_chunk1 = MagicMock()
            mock_chunk1.text = "Hello "
            mock_chunk2 = MagicMock()
            mock_chunk2.text = "World!"
            
            mock_client.generate_content.return_value = [mock_chunk1, mock_chunk2]
            
            # Mock the executor
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_in_executor = MagicMock(
                    return_value=[mock_chunk1, mock_chunk2]
                )
                
                tokens = []
                async for token in service.stream_blog_content("test prompt"):
                    tokens.append(token)
                
                assert tokens == ["Hello ", "World!"]
    
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
        with patch.object(service, '_initialize_client') as mock_init:
            info = await service.get_model_info("test-model")
            
            assert info["model"] == "test-model"
            assert info["provider"] == "google_gemini"
            assert info["status"] == "connected"
            assert "max_output_tokens" in info
            assert "temperature" in info
            assert "top_p" in info
            assert "top_k" in info
    
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
    async def test_stream_blog_from_gemini(self):
        """Test the backward compatibility function"""
        with patch('services.gemini_service.gemini_service') as mock_service:
            mock_service.stream_blog_content.return_value = iter(["token1", "token2"])
            
            tokens = []
            async for token in stream_blog_from_gemini("test prompt"):
                tokens.append(token)
            
            assert tokens == ["token1", "token2"]
            mock_service.stream_blog_content.assert_called_once_with("test prompt", "html")


class TestErrorHandling:
    """Test error handling scenarios"""
    
    @pytest.mark.asyncio
    async def test_connection_error(self):
        """Test handling of connection errors"""
        service = GeminiService()
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_get_client.side_effect = Exception("API connection refused")
            
            with pytest.raises(GeminiConnectionError, match="Failed to connect to Gemini"):
                await service._get_client("test-model")
    
    @pytest.mark.asyncio
    async def test_timeout_error(self):
        """Test handling of timeout errors"""
        service = GeminiService()
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            # Mock the executor to raise TimeoutError
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_in_executor = MagicMock(
                    side_effect=asyncio.TimeoutError()
                )
                
                with pytest.raises(GeminiTimeoutError):
                    async for _ in service.stream_blog_content("test prompt"):
                        pass
    
    @pytest.mark.asyncio
    async def test_generic_service_error(self):
        """Test handling of generic service errors"""
        service = GeminiService()
        
        with patch.object(service, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_get_client.return_value = mock_client
            
            # Mock the executor to raise generic exception
            with patch('asyncio.get_event_loop') as mock_loop:
                mock_loop.return_value.run_in_executor = MagicMock(
                    side_effect=Exception("Unknown error")
                )
                
                with pytest.raises(GeminiServiceError, match="Unexpected error"):
                    async for _ in service.stream_blog_content("test prompt"):
                        pass


class TestPromptTemplates:
    """Test prompt template functionality"""
    
    @pytest.mark.asyncio
    async def test_html_template_formatting(self):
        """Test HTML prompt template formatting"""
        from services.gemini_service import PROMPT_TEMPLATES
        
        prompt = "Test topic"
        formatted = PROMPT_TEMPLATES["html"].format(user_prompt=prompt)
        
        assert prompt in formatted
        assert "HTML5" in formatted
        assert "html" in formatted.lower()
    
    @pytest.mark.asyncio
    async def test_markdown_template_formatting(self):
        """Test Markdown prompt template formatting"""
        from services.gemini_service import PROMPT_TEMPLATES
        
        prompt = "Test topic"
        formatted = PROMPT_TEMPLATES["markdown"].format(user_prompt=prompt)
        
        assert prompt in formatted
        assert "Markdown" in formatted
        assert "markdown" in formatted.lower()
    
    @pytest.mark.asyncio
    async def test_plain_template_formatting(self):
        """Test plain text prompt template formatting"""
        from services.gemini_service import PROMPT_TEMPLATES
        
        prompt = "Test topic"
        formatted = PROMPT_TEMPLATES["plain"].format(user_prompt=prompt)
        
        assert prompt in formatted
        assert "article" in formatted.lower()


if __name__ == "__main__":
    pytest.main([__file__])
