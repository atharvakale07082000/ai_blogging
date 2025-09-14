import pytest
import os
from unittest.mock import patch
from config import Settings

def test_settings_validation():
    """Test that settings validation works correctly"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key_123',
        'ALLOWED_ORIGINS': 'http://localhost:3000,http://localhost:8080'
    }):
        settings = Settings()
        assert settings.OPENAI_API_KEY == 'test_key_123'
        assert 'http://localhost:3000' in settings.ALLOWED_ORIGINS

def test_invalid_openai_key():
    """Test that invalid OpenAI key raises error"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': '<YOUR_OPENAI_API_KEY>'
    }):
        with pytest.raises(ValueError, match="OPENAI_API_KEY must be set"):
            Settings()

def test_wildcard_origins():
    """Test that wildcard origins are rejected"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key_123',
        'ALLOWED_ORIGINS': '*'
    }):
        with pytest.raises(ValueError, match="Wildcard origins are not allowed"):
            Settings()

def test_default_values():
    """Test default configuration values"""
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test_key_123'
    }):
        settings = Settings()
        assert settings.HOST == "0.0.0.0"
        assert settings.PORT == 8000
        assert settings.RATE_LIMIT_PER_MINUTE == 60 