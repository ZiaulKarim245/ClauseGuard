"""
Configuration Management - Handles environment variables and system-wide settings.
"""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings powered by Pydantic BaseSettings.
    Automatically loads variables from the .env file.
    """
    # AI Provider Keys
    GROQ_API_KEY: str
    GOOGLE_API_KEY: str
    TAVILY_API_KEY: str
    
    # LangSmith Observability Context
    LANGCHAIN_TRACING_V2: str = "true"
    LANGCHAIN_API_KEY: str
    LANGCHAIN_PROJECT: str
    
    # Filesystem Architecture
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    DATA_DIR: str = os.path.join(BASE_DIR, "data")
    UPLOAD_DIR: str = os.path.join(DATA_DIR, "temp")
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

# Singleton instance for high-performance access across the application
settings = Settings()