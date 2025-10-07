"""
Application Configuration
Environment-specific settings using Pydantic BaseSettings
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Tell Pydantic to look for environment variables defined in a .env file
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # App Settings
    app_name: str = "Impact Realty AI Platform"
    environment: str = "development"
    debug: bool = True

    # API Settings
    allowed_origins: List[str] = ["*"]
    api_key: str = ""

    # Database - CORRECTED: Reads from POSTGRES_URL
    postgres_url: str = ""

    # Azure Settings
    azure_key_vault_url: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_tenant_id: str = ""

    # Zoho Settings - CORRECTED: Reads from ZOHO_... variables
    zoho_client_id: str = ""
    zoho_client_secret: str = ""
    zoho_refresh_token: str = ""
    zoho_crm_base_url: str = "https://www.zohoapis.com"

    # LangFlow Settings
    langflow_base_url: str = "http://localhost:7860"
    langflow_api_key: str = ""

    # SMS Settings (SalesMsg) - CORRECTED: Reads from SALESMSG_API_TOKEN
    salesmsg_api_token: str = ""
    salesmsg_base_url: str = "https://api.salesmsg.com/v1"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings"""
    return Settings()
