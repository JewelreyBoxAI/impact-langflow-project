"""
MCP (Model Context Protocol) API Routes
MCP server integration endpoints for external service communication
"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

from ...services.mcp_service import MCPService
from ...schemas.mcp_schemas import (
    MCPServerStatus, MCPRequest, MCPResponse,
    MCPDedupeRequest, MCPDedupeResponse
)
from ...api.dependencies import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

def get_mcp_service():
    """Dependency to get MCP service instance"""
    return MCPService()

@router.get("/servers/status", response_model=List[MCPServerStatus])
async def get_mcp_servers_status(
    current_user: dict = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """Get status of all MCP servers"""
    try:
        status = await mcp_service.get_all_servers_status()
        return status
    except Exception as e:
        logger.error(f"Error getting MCP servers status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/servers/{server_name}/restart")
async def restart_mcp_server(
    server_name: str,
    current_user: dict = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """Restart specific MCP server"""
    try:
        result = await mcp_service.restart_server(server_name)
        return {
            "server_name": server_name,
            "status": "restarted",
            "message": f"MCP server {server_name} restarted successfully",
            "timestamp": datetime.utcnow().isoformat(),
            "details": result
        }
    except Exception as e:
        logger.error(f"Error restarting MCP server {server_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/zoho/dedupe", response_model=MCPDedupeResponse)
async def zoho_dedupe_prospects(
    request: MCPDedupeRequest,
    current_user: dict = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """Deduplicate prospects against Zoho CRM via MCP"""
    try:
        logger.info(f"Deduplicating {len(request.prospects)} prospects via Zoho MCP")

        result = await mcp_service.dedupe_zoho_prospects(
            prospects=request.prospects,
            dedupe_fields=request.dedupe_fields
        )

        return MCPDedupeResponse(
            unique_prospects=result.get("unique_prospects", []),
            duplicates=result.get("duplicates", []),
            duplicates_count=len(result.get("duplicates", [])),
            unique_count=len(result.get("unique_prospects", [])),
            processing_time=result.get("processing_time", 0)
        )

    except Exception as e:
        logger.error(f"Error in Zoho MCP deduplication: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/request", response_model=MCPResponse)
async def send_mcp_request(
    request: MCPRequest,
    current_user: dict = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """Send generic MCP request to specified server"""
    try:
        result = await mcp_service.send_request(
            server_name=request.server_name,
            method=request.method,
            params=request.params
        )

        return MCPResponse(
            server_name=request.server_name,
            method=request.method,
            success=result.get("success", False),
            result=result.get("result"),
            error=result.get("error"),
            timestamp=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error(f"Error sending MCP request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/servers/{server_name}/health")
async def check_server_health(
    server_name: str,
    current_user: dict = Depends(get_current_user),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """Check health of specific MCP server"""
    try:
        health = await mcp_service.check_server_health(server_name)
        return {
            "server_name": server_name,
            "healthy": health.get("healthy", False),
            "response_time": health.get("response_time", 0),
            "last_check": datetime.utcnow().isoformat(),
            "details": health.get("details", {})
        }
    except Exception as e:
        logger.error(f"Error checking server health: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))