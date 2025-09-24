"""
Health Check API Routes
System health and status endpoints
"""

from fastapi import APIRouter
from datetime import datetime

from ...integrations.azure.keyvault_client import keyvault_client
from ...services.zoho_service import ZohoService

router = APIRouter()


@router.get("/")
async def health_check():
    """Comprehensive health check endpoint"""
    timestamp = datetime.utcnow().isoformat()

    # Check Key Vault connectivity
    kv_health = keyvault_client.health_check()

    # Check Zoho credentials
    zoho_service = ZohoService()
    zoho_health = {
        "client_id": bool(zoho_service.client_id),
        "client_secret": bool(zoho_service.client_secret),
        "refresh_token": bool(zoho_service.refresh_token)
    }

    # Determine overall health
    overall_status = "healthy" if (
        kv_health["status"] == "healthy" and
        all(zoho_health.values())
    ) else "degraded"

    return {
        "status": overall_status,
        "timestamp": timestamp,
        "services": {
            "key_vault": kv_health,
            "zoho_credentials": zoho_health
        },
        "version": "1.0.0",
        "server": "Impact Realty AI Platform"
    }