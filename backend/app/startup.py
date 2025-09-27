"""
MCP Server startup configuration and initialization
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.keyvault_client import keyvault_client

def setup_logging():
    """Configure logging for the MCP server"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('mcp_server.log')
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(logging.WARNING)
    logging.getLogger("azure.identity").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

def validate_environment():
    """Validate that required environment variables and credentials are available"""
    logger = logging.getLogger(__name__)
    
    # Check Key Vault access
    kv_health = keyvault_client.health_check()
    if kv_health["status"] != "healthy":
        logger.warning(f"Key Vault health check failed: {kv_health['message']}")
        logger.info("Falling back to environment variables for credentials")
    else:
        logger.info("Key Vault connection successful")
    
    # Check for critical environment variables
    required_env_vars = [
        "AZURE_KEY_VAULT_NAME",
        "MCP_SERVER_PORT", 
        "MCP_SERVER_HOST"
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing environment variables: {', '.join(missing_vars)}")
        logger.info("Using default values where possible")
    
    # Check credentials availability
    zoho_creds = keyvault_client.get_zoho_credentials()
    ai_creds = keyvault_client.get_ai_credentials()
    
    cred_status = {
        "zoho_client_id": bool(zoho_creds.get("client_id")),
        "zoho_client_secret": bool(zoho_creds.get("client_secret")),
        "zoho_refresh_token": bool(zoho_creds.get("refresh_token")),
        "openai_api_key": bool(ai_creds.get("openai_api_key")),
        "anthropic_api_key": bool(ai_creds.get("anthropic_api_key"))
    }
    
    logger.info("Credential availability check:")
    for cred_name, available in cred_status.items():
        status = "✓" if available else "✗"
        logger.info(f"  {cred_name}: {status}")
    
    return cred_status

def get_server_config():
    """Get server configuration from environment/Key Vault"""
    return {
        "host": os.getenv("MCP_SERVER_HOST", "0.0.0.0"),
        "port": int(os.getenv("MCP_SERVER_PORT", "8000")),
        "reload": os.getenv("ENVIRONMENT", "development") == "development",
        "log_level": os.getenv("LOG_LEVEL", "info").lower()
    }

def initialize_server():
    """Initialize the MCP server with proper configuration"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Impact Realty MCP Server...")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Project root: {project_root}")
    
    # Validate environment
    cred_status = validate_environment()
    
    # Get server configuration
    config = get_server_config()
    logger.info(f"Server configuration: {config}")
    
    return config

if __name__ == "__main__":
    config = initialize_server()
    
    # Import and run the FastAPI app
    import uvicorn
    from mcp_server.main import app
    
    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
        reload=config["reload"],
        log_level=config["log_level"]
    )