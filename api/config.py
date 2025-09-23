#!/usr/bin/env python3
"""
Configuration settings for PDF Extractor Lambda
"""

import os
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Environment
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["https://localhost:3000"], 
        env="ALLOWED_ORIGINS",
        description="Comma-separated list of allowed origins"
    )
    
    # Authentication
    api_key_header: str = Field(default="X-API-KEY", env="API_KEY_HEADER")
    valid_api_keys: List[str] = Field(
        default=["2ZbAQyiEIz8hN4xsEsRfckbKPopB4snapYGobrXh"],
        env="VALID_API_KEYS",
        description="Comma-separated list of valid API keys"
    )

    # JWT Configuration (for more advanced auth)
    jwt_secret_key: str = Field(default="", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    
    # File Upload Limits
    max_file_size_mb: int = Field(default=25, env="MAX_FILE_SIZE_MB")  # Lambda has 50MB limit
    allowed_file_types: List[str] = Field(
        default=["application/pdf", "application/x-pdf"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, env="RATE_LIMIT_REQUESTS")
    rate_limit_window: int = Field(default=3600, env="RATE_LIMIT_WINDOW")  # 1 hour
    
    # AWS Configuration
    aws_region: str = Field(default="us-east-1", env="AWS_REGION")
    s3_bucket_name: str = Field(default="pdf-extractor-api-storage", env="S3_BUCKET_NAME")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    @field_validator('valid_api_keys', 'allowed_origins', 'allowed_file_types')
    @classmethod
    def parse_list_fields(cls, v):
        """Parse comma-separated environment variables into lists"""
        if isinstance(v, str):
            return [item.strip() for item in v.split(',') if item.strip()]
        return v
        
    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes"""
        return self.max_file_size_mb * 1024 * 1024
    

# Global settings instance
settings = Settings()