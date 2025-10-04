"""
LangFlow API Routes
LangFlow integration endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
import logging

from ...services.langflow_service import LangFlowService
from ...schemas.crm_schemas import FlowRunRequest, FlowRunResponse, FlowStatusResponse
from ...api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)


def get_langflow_service():
    """Dependency to get LangFlow service instance"""
    return LangFlowService()


@router.post("/run", response_model=FlowRunResponse)
async def run_flow(
    request: FlowRunRequest,
    current_user: dict = Depends(get_current_user),
    langflow_service: LangFlowService = Depends(get_langflow_service)
):
    """Execute a LangFlow with given parameters"""
    try:
        logger.info(f"Running LangFlow {request.flow_id} with params: {request.parameters}")

        result = await langflow_service.run_flow(
            flow_id=request.flow_id,
            parameters=request.parameters
        )

        return FlowRunResponse(
            flow_id=request.flow_id,
            execution_id=result.get("execution_id"),
            status="started",
            result=result,
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error running flow {request.flow_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{execution_id}", response_model=FlowStatusResponse)
async def get_flow_status(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
    langflow_service: LangFlowService = Depends(get_langflow_service)
):
    """Get status of a running LangFlow execution"""
    try:
        status = await langflow_service.get_flow_status(execution_id)

        return FlowStatusResponse(
            execution_id=execution_id,
            status=status.get("status", "unknown"),
            result=status.get("result"),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error getting flow status {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))