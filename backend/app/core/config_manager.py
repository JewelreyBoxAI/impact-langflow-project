"""
Standardized Configuration Management for AI/ML Pipeline Components
Centralized configuration handling with environment-specific overrides and validation
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
from functools import lru_cache

from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

@dataclass
class ComponentConfig:
    """Base configuration class for AI/ML components"""
    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    health_check_url: Optional[str] = None
    retry_config: Dict[str, Any] = field(default_factory=lambda: {
        "max_retries": 3,
        "retry_delay": 1.0,
        "exponential_backoff": True
    })

class DatabaseConfig(BaseModel):
    """Database configuration"""
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(10, description="Connection pool size")
    max_overflow: int = Field(20, description="Maximum pool overflow")
    pool_timeout: int = Field(30, description="Pool timeout in seconds")
    echo: bool = Field(False, description="Enable SQL query logging")

class ZohoConfig(BaseModel):
    """Zoho CRM and API configuration"""
    client_id: str = Field(..., description="Zoho OAuth Client ID")
    client_secret: str = Field(..., description="Zoho OAuth Client Secret")
    refresh_token: str = Field(..., description="Zoho OAuth Refresh Token")
    access_token: Optional[str] = Field(None, description="Current access token")
    crm_base_url: str = Field("https://www.zohoapis.com/crm/v2", description="Zoho CRM API base URL")
    auth_url: str = Field("https://accounts.zoho.com/oauth/v2/token", description="Zoho OAuth URL")
    redirect_url: str = Field("http://127.0.0.1:8787/oauth", description="OAuth redirect URL")
    rate_limit_per_minute: int = Field(100, description="API rate limit per minute")
    timeout: int = Field(30, description="Request timeout in seconds")

    @validator('client_id', 'client_secret', 'refresh_token')
    def validate_required_fields(cls, v):
        if not v or v == "Generate-from-OAuth":
            raise ValueError("Required Zoho credential not configured")
        return v

class LangFlowConfig(BaseModel):
    """LangFlow integration configuration"""
    base_url: str = Field("http://localhost:7860", description="LangFlow server URL")
    api_key: Optional[str] = Field(None, description="LangFlow API key")
    flows_directory: str = Field("./flows", description="Directory containing flow definitions")
    default_flow_id: str = Field("recruiting-flow", description="Default flow to use")
    timeout: int = Field(60, description="Flow execution timeout")
    max_concurrent_flows: int = Field(5, description="Maximum concurrent flow executions")

class MCPServerConfig(BaseModel):
    """MCP Server configuration"""
    enabled: bool = Field(True, description="Enable MCP server")
    host: str = Field("0.0.0.0", description="Server host")
    port: int = Field(3002, description="Server port")
    api_key: str = Field("dev-mcp-key-change-in-production", description="MCP API key")
    cors_origins: List[str] = Field(["http://localhost:3000", "https://langflow.org"], description="CORS allowed origins")
    ssl_cert_path: Optional[str] = Field(None, description="SSL certificate path")
    ssl_key_path: Optional[str] = Field(None, description="SSL key path")
    upload_dir: str = Field("./uploads", description="File upload directory")
    max_file_size: int = Field(50 * 1024 * 1024, description="Maximum file size in bytes")
    allowed_extensions: List[str] = Field([".pdf", ".doc", ".docx", ".txt", ".csv", ".xlsx", ".jpg", ".jpeg", ".png", ".gif"], description="Allowed file extensions")

class AzureConfig(BaseModel):
    """Azure services configuration"""
    key_vault_url: str = Field("", description="Azure Key Vault URL")
    client_id: str = Field("", description="Azure AD Client ID")
    client_secret: str = Field("", description="Azure AD Client Secret")
    tenant_id: str = Field("", description="Azure AD Tenant ID")
    enabled: bool = Field(False, description="Enable Azure Key Vault integration")

class AIModelConfig(BaseModel):
    """AI/ML Model configuration"""
    provider: str = Field("openai", description="Model provider (openai, anthropic, etc.)")
    model_name: str = Field("gpt-4", description="Model name/ID")
    api_key: str = Field(..., description="API key for the model provider")
    base_url: Optional[str] = Field(None, description="Custom API base URL")
    max_tokens: int = Field(4000, description="Maximum tokens per request")
    temperature: float = Field(0.7, description="Model temperature")
    timeout: int = Field(60, description="Request timeout")
    rate_limit_rpm: int = Field(100, description="Requests per minute limit")

class VectorDBConfig(BaseModel):
    """Vector Database configuration"""
    provider: str = Field("faiss", description="Vector DB provider (faiss, pinecone, weaviate, chroma)")
    connection_string: Optional[str] = Field(None, description="Connection string for remote vector DBs")
    api_key: Optional[str] = Field(None, description="API key for vector DB service")
    index_name: str = Field("default", description="Index/collection name")
    dimension: int = Field(1536, description="Vector dimension")
    metric: str = Field("cosine", description="Distance metric")

class MemoryConfig(BaseModel):
    """Memory system configuration"""
    provider: str = Field("local", description="Memory provider (local, mem0, zep)")
    api_key: Optional[str] = Field(None, description="API key for memory service")
    session_timeout: int = Field(3600, description="Session timeout in seconds")
    max_memory_size: int = Field(1000, description="Maximum memory entries per session")

class MultimodalConfig(BaseModel):
    """Multimodal processing configuration"""
    speech_to_text_provider: str = Field("deepgram", description="STT provider")
    text_to_speech_provider: str = Field("elevenlabs", description="TTS provider")
    deepgram_api_key: Optional[str] = Field(None, description="Deepgram API key")
    elevenlabs_api_key: Optional[str] = Field(None, description="ElevenLabs API key")
    whisper_model: str = Field("base", description="Whisper model size")

class ApplicationConfig(BaseSettings):
    """Main application configuration"""

    # Application metadata
    app_name: str = Field("Impact Realty AI Platform", description="Application name")
    version: str = Field("2.0.0", description="Application version")
    environment: str = Field("development", description="Environment (development, staging, production)")
    debug: bool = Field(True, description="Debug mode")

    # Logging configuration
    log_level: str = Field("INFO", description="Logging level")
    log_file: str = Field("app.log", description="Log file path")
    log_format: str = Field("%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")

    # Security
    secret_key: str = Field("change-in-production", description="Application secret key")
    jwt_secret: str = Field("jwt-secret-change-in-production", description="JWT secret key")
    api_key: str = Field("", description="API key for external access")

    # Component configurations
    database: DatabaseConfig = Field(default_factory=lambda: DatabaseConfig(url="sqlite:///./app.db"))
    zoho: ZohoConfig = Field(default_factory=lambda: ZohoConfig(
        client_id=os.getenv("ZOHO_CLIENT_ID", ""),
        client_secret=os.getenv("ZOHO_CLIENT_SECRET", ""),
        refresh_token=os.getenv("ZOHO_REFRESH_TOKEN", "")
    ))
    langflow: LangFlowConfig = Field(default_factory=LangFlowConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    azure: AzureConfig = Field(default_factory=AzureConfig)
    ai_model: AIModelConfig = Field(default_factory=lambda: AIModelConfig(
        api_key=os.getenv("OPENAI_API_KEY", "")
    ))
    vector_db: VectorDBConfig = Field(default_factory=VectorDBConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    multimodal: MultimodalConfig = Field(default_factory=MultimodalConfig)

    class Config:
        env_file = [".env", ".env.local", ".env.production"]
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "allow"
        env_nested_delimiter = "__"

class ConfigManager:
    """Centralized configuration manager with validation and caching"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else Path("config.json")
        self._config: Optional[ApplicationConfig] = None
        self._component_configs: Dict[str, ComponentConfig] = {}

    @lru_cache(maxsize=1)
    def get_config(self) -> ApplicationConfig:
        """Get application configuration with caching"""
        if self._config is None:
            self._config = self._load_config()
        return self._config

    def _load_config(self) -> ApplicationConfig:
        """Load configuration from environment and files"""
        try:
            # Start with environment variables
            config = ApplicationConfig()

            # Override with config file if it exists
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    # Merge file config with environment config
                    config = ApplicationConfig.parse_obj({**config.dict(), **file_config})

            logger.info(f"Configuration loaded successfully for environment: {config.environment}")
            return config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            # Return default configuration as fallback
            return ApplicationConfig()

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []
        config = self.get_config()

        try:
            # Validate Zoho configuration
            if not config.zoho.client_id or config.zoho.client_id == "":
                issues.append("Zoho client_id not configured")

            if not config.zoho.client_secret or config.zoho.client_secret == "":
                issues.append("Zoho client_secret not configured")

            # Validate AI model configuration
            if not config.ai_model.api_key or config.ai_model.api_key == "":
                issues.append("AI model API key not configured")

            # Validate file upload directory
            upload_dir = Path(config.mcp_server.upload_dir)
            if not upload_dir.exists():
                try:
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    logger.info(f"Created upload directory: {upload_dir}")
                except Exception as e:
                    issues.append(f"Cannot create upload directory: {e}")

            # Validate database URL format
            if config.database.url and not any(config.database.url.startswith(scheme) for scheme in ["sqlite:", "postgresql:", "mysql:"]):
                issues.append("Invalid database URL format")

        except Exception as e:
            issues.append(f"Configuration validation error: {e}")

        return issues

    def get_component_config(self, component_name: str) -> Optional[ComponentConfig]:
        """Get configuration for a specific component"""
        return self._component_configs.get(component_name)

    def register_component(self, component_config: ComponentConfig):
        """Register a component configuration"""
        self._component_configs[component_config.name] = component_config
        logger.info(f"Registered component configuration: {component_config.name}")

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        config = self.get_config()
        issues = self.validate_config()

        return {
            "status": "healthy" if not issues else "degraded",
            "environment": config.environment,
            "version": config.version,
            "issues": issues,
            "components": {
                name: {
                    "enabled": comp.enabled,
                    "health_check_url": comp.health_check_url
                }
                for name, comp in self._component_configs.items()
            },
            "timestamp": str(datetime.now())
        }

    def export_config(self, output_path: Optional[str] = None) -> str:
        """Export current configuration to JSON file"""
        config = self.get_config()
        config_dict = config.dict()

        # Remove sensitive data
        sensitive_fields = ["api_key", "secret_key", "jwt_secret", "client_secret", "password"]
        self._redact_sensitive_data(config_dict, sensitive_fields)

        output_file = output_path or "config_export.json"
        with open(output_file, 'w') as f:
            json.dump(config_dict, f, indent=2, default=str)

        logger.info(f"Configuration exported to: {output_file}")
        return output_file

    def _redact_sensitive_data(self, data: Any, sensitive_fields: List[str]):
        """Recursively redact sensitive data from configuration"""
        if isinstance(data, dict):
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    data[key] = "***REDACTED***"
                else:
                    self._redact_sensitive_data(value, sensitive_fields)
        elif isinstance(data, list):
            for item in data:
                self._redact_sensitive_data(item, sensitive_fields)

# Global configuration manager instance
config_manager = ConfigManager()

def get_config() -> ApplicationConfig:
    """Get the global application configuration"""
    return config_manager.get_config()

def get_zoho_config() -> ZohoConfig:
    """Get Zoho-specific configuration"""
    return config_manager.get_config().zoho

def get_langflow_config() -> LangFlowConfig:
    """Get LangFlow-specific configuration"""
    return config_manager.get_config().langflow

def get_mcp_config() -> MCPServerConfig:
    """Get MCP server configuration"""
    return config_manager.get_config().mcp_server

def validate_environment() -> List[str]:
    """Validate the current environment configuration"""
    return config_manager.validate_config()

# Initialize logging based on configuration
def setup_logging():
    """Setup logging based on configuration"""
    config = get_config()

    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format=config.log_format,
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler()
        ]
    )

    logger.info(f"Logging configured for {config.environment} environment")

if __name__ == "__main__":
    # Test configuration loading
    setup_logging()
    config = get_config()
    issues = validate_environment()

    print(f"Configuration loaded for {config.environment} environment")
    print(f"Version: {config.version}")

    if issues:
        print(f"Configuration issues found:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ Configuration validation passed")