"""
Application Configuration
Environment-specific settings using Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # App Settings
    app_name: str = "Impact Realty AI Platform"
    environment: str = "development"
    debug: bool = True

    # API Settings
    allowed_origins: List[str] = ["*"]
    api_key: str = ""

    # Database
    database_url: str = ""

    # Azure Settings
    azure_key_vault_url: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = ""

    # Zoho Settings
    zoho_client_id: str = ""
    zoho_client_secret: str = ""
    zoho_refresh_token: str = ""
    zoho_api_base_url: str = "https://www.zohoapis.com"

    # LangFlow Settings
    langflow_base_url: str = "http://localhost:7860"
    langflow_api_key: str = ""

    # SMS Settings (SalesMsg)
    salesmsg_api_key: str = ""
    salesmsg_base_url: str = "https://api.salesmsg.com/v1"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()