import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "LIRA API"
    API_PREFIX: str = "/api/v1"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
    
    # Supabase Single Source of Truth
    SUPABASE_URL: str = ""
    SUPABASE_PUBLISHABLE_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    
    # Gemini API Link / Key
    GEMINI_API_KEY: str = ""
    
    # Voice Provider Configuration
    VOICE_PROVIDER: str = "mock"
    EXOTEL_API_KEY: str = ""
    EXOTEL_API_TOKEN: str = ""
    EXOTEL_ACCOUNT_SID: str = ""
    EXOTEL_CALLER_ID: str = ""
    EXOTEL_STREAM_URL: str = ""
    
    # Device Security
    DEVICE_TOKEN_PEPPER: str = "lira-device-secret-pepper"
    ENABLE_DEMO_SEED: bool = True
    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

settings = Settings()
