"""
Health Check API Routes
System health and status endpoints
"""

from fastapi import APIRouter
from datetime import datetime
from ...services.zoho_service import ZohoService

router = APIRouter()


@router.get("/")
async def health_check():
    """Comprehensive health check endpoint"""
    timestamp = datetime.utcnow().isoformat()

    # Key Vault check disabled (using .env instead)
    kv_health = {"status": "healthy", "message": "Using .env configuration"}

    # Check Zoho credentials
    try:
        zoho_service = ZohoService()
        zoho_health = {
            "client_id": bool(zoho_service.client_id),
            "client_secret": bool(zoho_service.client_secret),
            "refresh_token": bool(zoho_service.refresh_token)
        }
    except Exception as e:
        zoho_health = {"error": str(e)}

    # Determine overall health
    overall_status = "healthy" if (
        kv_health["status"] == "healthy" and
        all(zoho_health.values()) if isinstance(zoho_health, dict) and "error" not in zoho_health else False
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