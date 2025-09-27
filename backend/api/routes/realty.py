"""
Real Estate API Routes
Real estate specific business endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
import logging

from ...services.zoho_service import ZohoService
from ...schemas.crm_schemas import (
    PropertySearchRequest, AgentSearchRequest, CommissionCreateRequest,
    CRMSearchResponse, RecordResponse
)
from ...api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def get_zoho_service():
    """Dependency to get Zoho service instance"""
    return ZohoService()


@router.post("/properties/search", response_model=CRMSearchResponse)
async def search_properties(
    request: PropertySearchRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Search properties for Impact Realty"""
    try:
        properties = await zoho_service.search_properties(
            request.criteria, request.fields, request.page, request.per_page
        )

        return CRMSearchResponse(
            module="Properties",
            records=properties.get("data", []),
            total_count=properties.get("info", {}).get("count", 0),
            page=request.page,
            per_page=request.per_page
        )
    except Exception as e:
        logger.error(f"Error searching properties: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/search", response_model=CRMSearchResponse)
async def search_agents(
    request: AgentSearchRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Search real estate agents"""
    try:
        agents = await zoho_service.search_agents(
            request.criteria, request.fields, request.page, request.per_page
        )

        return CRMSearchResponse(
            module="Agents",
            records=agents.get("data", []),
            total_count=agents.get("info", {}).get("count", 0),
            page=request.page,
            per_page=request.per_page
        )
    except Exception as e:
        logger.error(f"Error searching agents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commissions/create", response_model=RecordResponse)
async def create_commission_record(
    request: CommissionCreateRequest,
    current_user: dict = Depends(get_current_user),
    zoho_service: ZohoService = Depends(get_zoho_service)
):
    """Create commission record for agent"""
    try:
        result = await zoho_service.create_commission_record(
            request.agent_id,
            request.deal_id,
            request.commission_amount,
            request.commission_data
        )

        return RecordResponse(
            record_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            module="Commissions",
            operation="create",
            details=result
        )
    except Exception as e:
        logger.error(f"Error creating commission record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))