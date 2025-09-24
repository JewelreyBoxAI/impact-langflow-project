"""
Azure Key Vault client for secure credential management
"""

import os
import logging
from typing import Optional, Dict, Any
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from functools import lru_cache

logger = logging.getLogger(__name__)

class KeyVaultClient:
    """Azure Key Vault client for secure credential retrieval"""
    
    def __init__(self):
        self.key_vault_name = os.getenv("AZURE_KEY_VAULT_NAME", "kv-impact-platform-v2")
        self.key_vault_url = f"https://{self.key_vault_name}.vault.azure.net/"
        
        try:
            # Use DefaultAzureCredential for authentication
            credential = DefaultAzureCredential()
            self.client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            logger.info(f"Initialized Key Vault client for {self.key_vault_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {str(e)}")
            self.client = None
    
    @lru_cache(maxsize=100)
    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Get secret from Key Vault with caching
        
        Args:
            secret_name: Name of the secret in Key Vault
            
        Returns:
            Secret value or None if not found/error
        """
        if not self.client:
            logger.warning("Key Vault client not initialized, falling back to environment variables")
            return os.getenv(secret_name.upper().replace('-', '_'))
        
        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"Successfully retrieved secret: {secret_name}")
            return secret.value
        except Exception as e:
            logger.error(f"Failed to retrieve secret {secret_name}: {str(e)}")
            # Fallback to environment variable
            env_var_name = secret_name.upper().replace('-', '_')
            fallback_value = os.getenv(env_var_name)
            if fallback_value:
                logger.info(f"Using fallback environment variable for {secret_name}")
            return fallback_value
    
    def get_zoho_credentials(self) -> Dict[str, Optional[str]]:
        """Get all Zoho credentials from Key Vault"""
        return {
            "client_id": self.get_secret("zoho-client-id"),
            "client_secret": self.get_secret("zoho-client-secret"), 
            "refresh_token": self.get_secret("zoho-refresh-token"),
            "access_token": self.get_secret("zoho-access-token")
        }
    
    def get_database_credentials(self) -> Dict[str, Optional[str]]:
        """Get database credentials from Key Vault"""
        return {
            "postgres_url": self.get_secret("postgres-url"),
            "postgres_host": self.get_secret("postgres-host"),
            "postgres_user": self.get_secret("postgres-user"),
            "postgres_password": self.get_secret("postgres-password"),
            "redis_url": self.get_secret("redis-url"),
            "redis_password": self.get_secret("redis-password")
        }
    
    def get_communication_credentials(self) -> Dict[str, Optional[str]]:
        """Get communication service credentials from Key Vault"""
        return {
            "salesmsg_api_token": self.get_secret("salesmsg-api-token"),
            "manychat_api_token": self.get_secret("manychat-api-token"),
            "twilio_account_sid": self.get_secret("twilio-account-sid"),
            "twilio_auth_token": self.get_secret("twilio-auth-token"),
            "twilio_phone_number": self.get_secret("twilio-phone-number")
        }
    
    def get_ai_credentials(self) -> Dict[str, Optional[str]]:
        """Get AI service credentials from Key Vault"""
        return {
            "openai_api_key": self.get_secret("openai-api-key"),
            "anthropic_api_key": self.get_secret("anthropic-api-key"),
            "langflow_api_key": self.get_secret("langflow-api-key")
        }
    
    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Set/update a secret in Key Vault
        
        Args:
            secret_name: Name of the secret
            secret_value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.client:
            logger.error("Key Vault client not initialized, cannot set secret")
            return False
        
        try:
            self.client.set_secret(secret_name, secret_value)
            logger.info(f"Successfully set secret: {secret_name}")
            
            # Clear cache for this secret
            if hasattr(self.get_secret, 'cache_info'):
                # Clear specific cache entry if possible (Python 3.9+)
                try:
                    self.get_secret.cache_clear()
                except:
                    pass
            
            return True
        except Exception as e:
            logger.error(f"Failed to set secret {secret_name}: {str(e)}")
            return False
    
    def list_secrets(self) -> list:
        """List all secrets in the Key Vault"""
        if not self.client:
            logger.error("Key Vault client not initialized")
            return []
        
        try:
            secrets = []
            for secret_properties in self.client.list_properties_of_secrets():
                secrets.append({
                    "name": secret_properties.name,
                    "enabled": secret_properties.enabled,
                    "created_on": secret_properties.created_on,
                    "updated_on": secret_properties.updated_on
                })
            return secrets
        except Exception as e:
            logger.error(f"Failed to list secrets: {str(e)}")
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check Key Vault connectivity and permissions"""
        if not self.client:
            return {
                "status": "error",
                "message": "Key Vault client not initialized",
                "vault_url": self.key_vault_url
            }
        
        try:
            # Try to list secrets as a connectivity/permission test
            list(self.client.list_properties_of_secrets(max_page_size=1))
            return {
                "status": "healthy",
                "message": "Key Vault connection successful",
                "vault_url": self.key_vault_url,
                "vault_name": self.key_vault_name
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Key Vault connection failed: {str(e)}",
                "vault_url": self.key_vault_url
            }

# Global instance
keyvault_client = KeyVaultClient()