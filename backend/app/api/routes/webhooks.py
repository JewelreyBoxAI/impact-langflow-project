"""
Webhook and Notification API Routes
External webhook and email integration endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from ...services.zoho_service import ZohoService
from ...schemas.crm_schemas import (
    WebhookCreateRequest, EmailSendRequest, StandardResponse
)
from ...api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def get_zoho_service():
    """Dependency to get Zoho service instance"""
    return ZohoService()


@router.post("/create", response_model=StandardResponse)
async def create_webhook(
    request: WebhookCreateRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Create webhook in Zoho CRM"""
    try:
        result = await zoho_service.create_webhook(request.webhook_data)

        return StandardResponse(
            success=True,
            data=result,
            message="Webhook created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/email/send", response_model=StandardResponse)
async def send_email(
    request: EmailSendRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Send email using Zoho CRM templates"""
    try:
        result = await zoho_service.send_email(
            request.template_id,
            request.recipient_emails,
            request.merge_data,
            request.related_record_id
        )

        return StandardResponse(
            success=True,
            data=result,
            message="Email sent successfully"
        )
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))