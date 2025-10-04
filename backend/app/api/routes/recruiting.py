"""
Recruiting API Routes
Complete recruiting workflow endpoints for Impact Realty
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json
import asyncio
import pandas as pd
import uuid
from io import StringIO, BytesIO

from ...services.recruiting_service import RecruitingService
from ...services.langflow_service import LangFlowService
from ...services.zoho_service import ZohoService
from ...schemas.recruiting_schemas import (
    RecruitingFlowRequest, RecruitingFlowResponse, ProspectUploadResponse,
    ProspectValidationRequest, ProspectValidationResponse, OutreachRequest,
    OutreachResponse, FlowExecutionStatus, RecruitingAnalytics, ChatMessage
)
from ...api.dependencies import get_current_user
from ...integrations.zoho.client import ZohoClient

router = APIRouter()
logger = logging.getLogger(__name__)

# WebSocket connection manager for real-time chat
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_message(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(message)
            except:
                self.disconnect(session_id)

manager = ConnectionManager()

def get_recruiting_service():
    """Dependency to get recruiting service instance"""
    return RecruitingService()

def get_langflow_service():
    """Dependency to get LangFlow service instance"""
    return LangFlowService()

def get_zoho_service():
    """Dependency to get Zoho service instance"""
    return ZohoService()

def get_zoho_mcp_client():
    """Dependency to get Zoho MCP client instance"""
    return ZohoClient()

# CATEGORY 1: RECRUITING FLOW EXECUTION

@router.post("/flow/execute", response_model=RecruitingFlowResponse)
async def execute_recruiting_flow(
    request: RecruitingFlowRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Execute complete recruiting flow with prospect data"""
    try:
        logger.info(f"Executing recruiting flow for user {current_user.get('user_id')} with {len(request.prospects)} prospects")

        # Generate execution ID
        execution_id = str(uuid.uuid4())

        # Start flow execution in background
        background_tasks.add_task(
            recruiting_service.execute_complete_flow,
            execution_id, request.prospects, request.flow_config, current_user
        )

        return RecruitingFlowResponse(
            execution_id=execution_id,
            status="started",
            prospects_count=len(request.prospects),
            estimated_completion=datetime.utcnow().isoformat(),
            message="Recruiting flow started successfully"
        )

    except Exception as e:
        logger.error(f"Error executing recruiting flow: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prospects/upload", response_model=ProspectUploadResponse)
async def upload_prospect_data(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Upload and validate CSV prospect data"""
    try:
        logger.info(f"Processing prospect upload: {file.filename}")

        # Validate file type
        if not file.filename.endswith(('.csv', '.xlsx', '.txt')):
            raise HTTPException(status_code=400, detail="Only CSV, XLSX, and TXT files are supported")

        # Read file content
        content = await file.read()

        # Process based on file type
        if file.filename.endswith('.csv'):
            df = pd.read_csv(StringIO(content.decode('utf-8')))
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(BytesIO(content))
        else:  # txt
            # Assume plain text format
            text_content = content.decode('utf-8')
            prospects = recruiting_service.parse_text_prospects(text_content)
            return ProspectUploadResponse(
                file_id=str(uuid.uuid4()),
                total_prospects=len(prospects),
                valid_prospects=len(prospects),
                invalid_prospects=0,
                validation_errors=[],
                prospects=prospects
            )

        # Validate prospect data
        validation_result = recruiting_service.validate_prospect_dataframe(df)

        return ProspectUploadResponse(
            file_id=str(uuid.uuid4()),
            total_prospects=len(df),
            valid_prospects=len(validation_result.get("valid_prospects", [])),
            invalid_prospects=len(validation_result.get("invalid_prospects", [])),
            validation_errors=validation_result.get("errors", []),
            prospects=validation_result.get("valid_prospects", [])
        )

    except Exception as e:
        logger.error(f"Error uploading prospects: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flow/status/{execution_id}", response_model=FlowExecutionStatus)
async def get_flow_status(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Get real-time flow execution status"""
    try:
        status = await recruiting_service.get_flow_execution_status(execution_id)

        return FlowExecutionStatus(
            execution_id=execution_id,
            status=status.get("status", "unknown"),
            progress_percentage=status.get("progress", 0),
            current_step=status.get("current_step", ""),
            completed_prospects=status.get("completed_prospects", 0),
            failed_prospects=status.get("failed_prospects", 0),
            results=status.get("results", {}),
            error_messages=status.get("errors", [])
        )

    except Exception as e:
        logger.error(f"Error getting flow status {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/prospects/validate", response_model=ProspectValidationResponse)
async def validate_prospect_data(
    request: ProspectValidationRequest,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Validate individual prospect data"""
    try:
        validation_result = recruiting_service.validate_single_prospect(request.prospect_data)

        return ProspectValidationResponse(
            is_valid=validation_result.get("is_valid", False),
            validated_prospect=validation_result.get("validated_prospect"),
            validation_errors=validation_result.get("errors", []),
            suggestions=validation_result.get("suggestions", [])
        )

    except Exception as e:
        logger.error(f"Error validating prospect: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flow/history")
async def get_flow_history(
    page: int = 1,
    per_page: int = 20,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Get recruiting flow execution history"""
    try:
        history = await recruiting_service.get_flow_history(
            user_id=current_user.get("user_id"),
            page=page,
            per_page=per_page
        )

        return {
            "executions": history.get("executions", []),
            "total_count": history.get("total_count", 0),
            "page": page,
            "per_page": per_page
        }

    except Exception as e:
        logger.error(f"Error getting flow history: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/flow/retry")
async def retry_flow_execution(
    execution_id: str,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Retry failed recruiting flow steps"""
    try:
        retry_result = await recruiting_service.retry_flow_execution(execution_id)

        return {
            "execution_id": execution_id,
            "retry_status": "started",
            "message": "Flow retry initiated successfully",
            "retry_details": retry_result
        }

    except Exception as e:
        logger.error(f"Error retrying flow {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# CATEGORY 2: OUTREACH MANAGEMENT

@router.post("/outreach/sms", response_model=OutreachResponse)
async def send_sms_outreach(
    request: OutreachRequest,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Send SMS via SalesMsg integration"""
    try:
        logger.info(f"Sending SMS to {request.recipient}")

        result = await recruiting_service.send_sms_outreach(
            recipient=request.recipient,
            message=request.message,
            prospect_data=request.prospect_data,
            user_id=current_user.get("user_id")
        )

        return OutreachResponse(
            outreach_id=result.get("outreach_id"),
            channel="sms",
            status="sent",
            recipient=request.recipient,
            sent_at=datetime.utcnow().isoformat(),
            details=result
        )

    except Exception as e:
        logger.error(f"Error sending SMS: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/outreach/email", response_model=OutreachResponse)
async def send_email_outreach(
    request: OutreachRequest,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Send email via Gmail integration"""
    try:
        logger.info(f"Sending email to {request.recipient}")

        result = await recruiting_service.send_email_outreach(
            recipient=request.recipient,
            subject=request.subject,
            message=request.message,
            prospect_data=request.prospect_data,
            user_id=current_user.get("user_id")
        )

        return OutreachResponse(
            outreach_id=result.get("outreach_id"),
            channel="email",
            status="sent",
            recipient=request.recipient,
            sent_at=datetime.utcnow().isoformat(),
            details=result
        )

    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/outreach/calendar", response_model=OutreachResponse)
async def schedule_calendar_meeting(
    request: OutreachRequest,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Schedule meetings via Zoho Calendar"""
    try:
        logger.info(f"Scheduling meeting with {request.recipient}")

        result = await recruiting_service.schedule_meeting(
            recipient=request.recipient,
            meeting_data=request.prospect_data,
            user_id=current_user.get("user_id")
        )

        return OutreachResponse(
            outreach_id=result.get("outreach_id"),
            channel="calendar",
            status="scheduled",
            recipient=request.recipient,
            sent_at=datetime.utcnow().isoformat(),
            details=result
        )

    except Exception as e:
        logger.error(f"Error scheduling meeting: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/outreach/status/{prospect_id}")
async def get_outreach_status(
    prospect_id: str,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Get outreach status for prospect"""
    try:
        status = await recruiting_service.get_prospect_outreach_status(prospect_id)

        return {
            "prospect_id": prospect_id,
            "outreach_history": status.get("outreach_history", []),
            "last_contact": status.get("last_contact"),
            "response_status": status.get("response_status"),
            "next_follow_up": status.get("next_follow_up")
        }

    except Exception as e:
        logger.error(f"Error getting outreach status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# CATEGORY 3: MCP SERVER INTEGRATION

@router.post("/mcp/zoho/dedupe")
async def zoho_dedupe_mcp(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user),
    mcp_client: ZohoClient = Depends(get_zoho_mcp_client)
):
    """MCP server for Zoho deduplication"""
    try:
        logger.info("Executing Zoho deduplication via MCP")

        result = await mcp_client.dedupe_prospects(request.get("prospects", []))

        return {
            "status": "success",
            "dedupe_results": result,
            "processed_count": len(request.get("prospects", [])),
            "duplicates_found": result.get("duplicates_count", 0)
        }

    except Exception as e:
        logger.error(f"Error in Zoho MCP dedupe: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/mcp/servers/status")
async def get_mcp_servers_status(
    current_user: dict = Depends(get_current_user),
    mcp_client: ZohoClient = Depends(get_zoho_mcp_client)
):
    """Get MCP server health status"""
    try:
        status = await mcp_client.health_check()

        return {
            "zoho_mcp": status,
            "servers_online": 1 if status.get("status") == "healthy" else 0,
            "last_check": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error checking MCP status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mcp/servers/restart")
async def restart_mcp_servers(
    current_user: dict = Depends(get_current_user),
    mcp_client: ZohoClient = Depends(get_zoho_mcp_client)
):
    """Restart MCP servers"""
    try:
        result = await mcp_client.restart_server()

        return {
            "status": "restarted",
            "message": "MCP servers restarted successfully",
            "restart_time": datetime.utcnow().isoformat(),
            "details": result
        }

    except Exception as e:
        logger.error(f"Error restarting MCP servers: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# CATEGORY 4: CHAT & SESSION MANAGEMENT

@router.post("/chat/message")
async def send_chat_message(
    message: ChatMessage,
    current_user: dict = Depends(get_current_user),
    langflow_service: LangFlowService = Depends(get_langflow_service)
):
    """Send message to recruiting agent"""
    try:
        logger.info(f"Processing chat message for session {message.session_id}")

        # Execute recruiting flow with chat message
        flow_result = await langflow_service.run_flow(
            flow_id="impact-realty-recruiting-flow",
            parameters={
                "input_value": message.content,
                "session_id": message.session_id,
                "user_id": current_user.get("user_id"),
                "sender": "User"
            }
        )

        # Send response via WebSocket if connected
        if message.session_id in manager.active_connections:
            await manager.send_message(message.session_id, {
                "type": "agent_response",
                "content": flow_result.get("response", ""),
                "timestamp": datetime.utcnow().isoformat()
            })

        return {
            "message_id": str(uuid.uuid4()),
            "session_id": message.session_id,
            "response": flow_result.get("response", ""),
            "status": "processed"
        }

    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.websocket("/chat/ws/{session_id}")
async def recruiting_chat_websocket(
    websocket: WebSocket,
    session_id: str,
    langflow_service: LangFlowService = Depends(get_langflow_service)
):
    """Real-time chat WebSocket connection"""
    try:
        await manager.connect(websocket, session_id)
        logger.info(f"WebSocket connected for session {session_id}")

        while True:
            # Receive message from client
            data = await websocket.receive_json()

            # Process message through recruiting flow
            if data.get("type") == "user_message":
                flow_result = await langflow_service.run_flow(
                    flow_id="impact-realty-recruiting-flow",
                    parameters={
                        "input_value": data.get("content", ""),
                        "session_id": session_id,
                        "sender": "User"
                    }
                )

                # Send agent response
                await manager.send_message(session_id, {
                    "type": "agent_response",
                    "content": flow_result.get("response", ""),
                    "timestamp": datetime.utcnow().isoformat()
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
        manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket error for session {session_id}: {str(e)}")
        manager.disconnect(session_id)

# CATEGORY 5: FILE & DATA MANAGEMENT

@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """General file upload handler"""
    try:
        # Generate unique file ID
        file_id = str(uuid.uuid4())

        # Read file content
        content = await file.read()

        # Store file (implement your storage logic here)
        # For now, return file metadata

        return {
            "file_id": file_id,
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type,
            "uploaded_at": datetime.utcnow().isoformat(),
            "user_id": current_user.get("user_id")
        }

    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/data/export")
async def export_recruiting_data(
    format: str = "csv",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Export recruiting data/reports"""
    try:
        export_data = await recruiting_service.export_recruiting_data(
            user_id=current_user.get("user_id"),
            format=format,
            date_from=date_from,
            date_to=date_to
        )

        if format == "csv":
            output = StringIO()
            export_data.to_csv(output, index=False)
            output.seek(0)

            return StreamingResponse(
                iter([output.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=recruiting_export.csv"}
            )

        return {"export_data": export_data.to_dict('records')}

    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# CATEGORY 6: MONITORING & ANALYTICS

@router.get("/analytics/dashboard", response_model=RecruitingAnalytics)
async def get_recruiting_analytics(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user),
    recruiting_service: RecruitingService = Depends(get_recruiting_service)
):
    """Recruiting performance analytics"""
    try:
        analytics = await recruiting_service.get_recruiting_analytics(
            user_id=current_user.get("user_id"),
            date_from=date_from,
            date_to=date_to
        )

        return RecruitingAnalytics(
            total_prospects=analytics.get("total_prospects", 0),
            successful_contacts=analytics.get("successful_contacts", 0),
            response_rate=analytics.get("response_rate", 0.0),
            conversion_rate=analytics.get("conversion_rate", 0.0),
            channel_performance=analytics.get("channel_performance", {}),
            daily_metrics=analytics.get("daily_metrics", []),
            top_performing_messages=analytics.get("top_messages", [])
        )

    except Exception as e:
        logger.error(f"Error getting recruiting analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))