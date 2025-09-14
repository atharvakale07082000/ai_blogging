import os
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import validator, root_validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    # LLM Provider Selection: "openai" or "gemini"
    LLM_PROVIDER: str = "gemini"
    
    # OpenAI Configuration
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o"

    # Google Gemini Configuration (using Google Generative AI package)
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_OUTPUT_TOKENS: int = 8192
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_TOP_P: float = 0.8
    GEMINI_TOP_K: int = 40
    
    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = False
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_CREDENTIALS: bool = True
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Image Generation
    IMAGE_GENERATION_ENABLED: bool = True
    IMAGE_API_URL: Optional[str] = None
    
    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3"
    OLLAMA_TIMEOUT: int = 300
    OLLAMA_MAX_RETRIES: int = 3
    OLLAMA_RETRY_DELAY: float = 1.0
    
    # Database (for future use)
    DATABASE_URL: Optional[str] = None
    
    @root_validator(pre=False)
    def validate_provider_and_keys(cls, values):
        provider = values.get("LLM_PROVIDER", "gemini").lower()
        openai_key = values.get("OPENAI_API_KEY")
        gemini_key = values.get("GEMINI_API_KEY")

        if provider == "openai":
            if not openai_key or openai_key == "<YOUR_OPENAI_API_KEY>":
                raise ValueError("When LLM_PROVIDER=openai, OPENAI_API_KEY must be set")
        elif provider == "gemini":
            if not gemini_key or gemini_key == "<YOUR_GEMINI_API_KEY>":
                raise ValueError("When LLM_PROVIDER=gemini, GEMINI_API_KEY must be set")
        else:
            raise ValueError("LLM_PROVIDER must be either 'openai' or 'gemini'")
        return values
    
    @validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v):
        if "*" in v:
            raise ValueError("Wildcard origins are not allowed for security reasons")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    # Convenience accessors for unified LLM configuration
    @property
    def LLM_API_KEY(self) -> str:
        return self.GEMINI_API_KEY if self.LLM_PROVIDER.lower() == "gemini" else self.OPENAI_API_KEY  # type: ignore

    @property
    def LLM_MODEL(self) -> str:
        return self.GEMINI_MODEL if self.LLM_PROVIDER.lower() == "gemini" else self.OPENAI_MODEL
    
    @property
    def LLM_CONFIG(self) -> dict:
        """Get LLM configuration based on the selected provider"""
        if self.LLM_PROVIDER.lower() == "gemini":
            return {
                "model": self.GEMINI_MODEL,
                "api_key": self.GEMINI_API_KEY,
                "max_output_tokens": self.GEMINI_MAX_OUTPUT_TOKENS,
                "temperature": self.GEMINI_TEMPERATURE,
                "top_p": self.GEMINI_TOP_P,
                "top_k": self.GEMINI_TOP_K
            }
        else:
            return {
                "model": self.OPENAI_MODEL,
                "api_key": self.OPENAI_API_KEY,
                "base_url": self.OPENAI_BASE_URL
            }

# Global settings instance
settings = Settings()