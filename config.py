"""
Production-Ready Configuration Management
Enterprise-grade settings with environment variable support
"""

import os
import json
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeminiConfig(BaseModel):
    """Gemini API Configuration"""
    api_key: str = Field(..., description="Google Gemini API Key")
    model: str = Field(default="gemini-1.5-flash", description="Model name")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=2048, ge=1, le=8192)


class RetryConfig(BaseModel):
    """Retry Logic Configuration"""
    max_retries: int = Field(default=3, ge=0, le=10)
    initial_delay: float = Field(default=1.0, ge=0.1, le=10.0)
    exponential_base: float = Field(default=2.0, ge=1.0, le=5.0)
    max_delay: float = Field(default=60.0, ge=1.0, le=300.0)


class APIConfig(BaseModel):
    """FastAPI Server Configuration"""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)
    workers: int = Field(default=4, ge=1, le=32)
    reload: bool = Field(default=False)


class LogConfig(BaseModel):
    """Logging Configuration"""
    level: str = Field(default="INFO")
    file: str = Field(default="travel_assistant.log")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    max_bytes: int = Field(default=10485760)  # 10MB
    backup_count: int = Field(default=5)


class CORSConfig(BaseModel):
    """CORS Configuration"""
    origins: List[str] = Field(default=["http://localhost:3000", "http://localhost:8000"])
    allow_credentials: bool = Field(default=True)
    allow_methods: List[str] = Field(default=["*"])
    allow_headers: List[str] = Field(default=["*"])


class RateLimitConfig(BaseModel):
    """Rate Limiting Configuration"""
    enabled: bool = Field(default=True)
    requests: int = Field(default=100, ge=1)
    period: int = Field(default=60, ge=1)  # seconds


class CacheConfig(BaseModel):
    """Caching Configuration"""
    enabled: bool = Field(default=True)
    ttl: int = Field(default=3600, ge=0)  # seconds


class MonitoringConfig(BaseModel):
    """Monitoring & Observability Configuration"""
    enable_metrics: bool = Field(default=True)
    enable_tracing: bool = Field(default=True)
    metrics_port: int = Field(default=9090, ge=1, le=65535)


class SecurityConfig(BaseModel):
    """Security Configuration"""
    api_key_header: str = Field(default="X-API-Key")
    enable_api_key_auth: bool = Field(default=False)


class AppConfig(BaseModel):
    """Main Application Configuration"""
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    gemini: GeminiConfig
    retry: RetryConfig
    api: APIConfig
    logging: LogConfig
    cors: CORSConfig
    rate_limit: RateLimitConfig
    cache: CacheConfig
    monitoring: MonitoringConfig
    security: SecurityConfig


def load_config() -> AppConfig:
    """
    Load configuration from environment variables
    
    Returns:
        AppConfig: Complete application configuration
    """
    # Parse JSON arrays from environment
    def parse_json_list(value: str, default: List[str]) -> List[str]:
        try:
            return json.loads(value) if value else default
        except json.JSONDecodeError:
            return default
    
    config = AppConfig(
        environment=os.getenv("ENVIRONMENT", "development"),
        debug=os.getenv("DEBUG", "false").lower() == "true",
        
        gemini=GeminiConfig(
            api_key=os.getenv("GOOGLE_API_KEY", ""),
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
        ),
        
        retry=RetryConfig(
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
            initial_delay=float(os.getenv("INITIAL_RETRY_DELAY", "1.0")),
            exponential_base=float(os.getenv("RETRY_EXPONENTIAL_BASE", "2.0")),
            max_delay=float(os.getenv("MAX_RETRY_DELAY", "60.0"))
        ),
        
        api=APIConfig(
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            workers=int(os.getenv("API_WORKERS", "4")),
            reload=os.getenv("API_RELOAD", "false").lower() == "true"
        ),
        
        logging=LogConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file=os.getenv("LOG_FILE", "travel_assistant.log"),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            max_bytes=int(os.getenv("LOG_MAX_BYTES", "10485760")),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        ),
        
        cors=CORSConfig(
            origins=parse_json_list(os.getenv("CORS_ORIGINS"), ["http://localhost:3000", "http://localhost:8000"]),
            allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
            allow_methods=parse_json_list(os.getenv("CORS_ALLOW_METHODS"), ["*"]),
            allow_headers=parse_json_list(os.getenv("CORS_ALLOW_HEADERS"), ["*"])
        ),
        
        rate_limit=RateLimitConfig(
            enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            requests=int(os.getenv("RATE_LIMIT_REQUESTS", "100")),
            period=int(os.getenv("RATE_LIMIT_PERIOD", "60"))
        ),
        
        cache=CacheConfig(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            ttl=int(os.getenv("CACHE_TTL", "3600"))
        ),
        
        monitoring=MonitoringConfig(
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            metrics_port=int(os.getenv("METRICS_PORT", "9090"))
        ),
        
        security=SecurityConfig(
            api_key_header=os.getenv("API_KEY_HEADER", "X-API-Key"),
            enable_api_key_auth=os.getenv("ENABLE_API_KEY_AUTH", "false").lower() == "true"
        )
    )
    
    return config


# Global configuration instance
settings = load_config()


# Validate critical settings
if not settings.gemini.api_key or settings.gemini.api_key == "your_google_api_key_here":
    raise ValueError(
        "GOOGLE_API_KEY not configured. Please set it in .env file. "
        "Get your API key from: https://makersuite.google.com/app/apikey"
    )


if __name__ == "__main__":
    # Display configuration (for debugging)
    print("="*60)
    print("TRAVEL ASSISTANT - CONFIGURATION")
    print("="*60)
    print(f"Environment: {settings.environment}")
    print(f"Debug Mode: {settings.debug}")
    print(f"Gemini Model: {settings.gemini.model}")
    print(f"API Port: {settings.api.port}")
    print(f"Log Level: {settings.logging.level}")
    print(f"Rate Limiting: {'Enabled' if settings.rate_limit.enabled else 'Disabled'}")
    print(f"Caching: {'Enabled' if settings.cache.enabled else 'Disabled'}")
    print(f"Metrics: {'Enabled' if settings.monitoring.enable_metrics else 'Disabled'}")
    print("="*60)
