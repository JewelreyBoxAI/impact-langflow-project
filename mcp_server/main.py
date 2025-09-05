"""
FastAPI MCP Server for Impact Realty AI Platform
Provides Zoho integration tools for LangFlow agents
"""

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from .zoho_client import ZohoClient
from .keyvault_client import keyvault_client
from .schemas import (
    # Flow schemas
    FlowRunRequest, FlowRunResponse, FlowStatusResponse,
    # Basic CRM schemas
    CRMSearchRequest, CRMSearchResponse, CRMUpsertRequest, CRMUpsertResponse,
    # Enhanced CRM schemas
    CRMRecordGetRequest, CRMRecordsListRequest, CRMRecordUpdateRequest, CRMRecordDeleteRequest,
    LeadConvertRequest, RelatedRecordsRequest, ActivityCreateRequest, BulkReadRequest,
    FieldMetadataRequest, ModuleMetadataRequest,
    # Real Estate schemas
    PropertySearchRequest, AgentSearchRequest, CommissionCreateRequest,
    # Notification schemas
    WebhookCreateRequest, EmailSendRequest,
    # Activity schemas
    NotesCreateRequest, NotesCreateResponse, TasksCreateRequest, TasksCreateResponse,
    BlueprintTransitionRequest, BlueprintTransitionResponse,
    FilesAttachRequest, FilesAttachResponse,
    # Response schemas
    StandardResponse, RecordResponse, MetadataResponse, ErrorResponse
)

app = FastAPI(
    title="Impact Realty MCP Server",
    description="MCP server providing Zoho integration tools for LangFlow agents",
    version="1.0.0"
)

security = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

zoho_client = ZohoClient()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Validate API token - placeholder for actual auth"""
    # TODO: Implement proper authentication
    return {"user_id": "system"}

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    timestamp = datetime.utcnow().isoformat()
    
    # Check Key Vault connectivity
    kv_health = keyvault_client.health_check()
    
    # Check Zoho credentials
    zoho_health = {
        "client_id": bool(zoho_client.client_id),
        "client_secret": bool(zoho_client.client_secret),
        "refresh_token": bool(zoho_client.refresh_token)
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
        "server": "Impact Realty MCP Server"
    }

@app.post("/zoho/flow/run", response_model=FlowRunResponse)
async def run_zoho_flow(
    request: FlowRunRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute a Zoho Flow with given parameters"""
    try:
        logger.info(f"Running Zoho flow {request.flow_id} with params: {request.parameters}")
        
        result = await zoho_client.run_flow(
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

@app.get("/zoho/flow/status/{execution_id}", response_model=FlowStatusResponse)
async def get_flow_status(
    execution_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get status of a running Zoho Flow execution"""
    try:
        status = await zoho_client.get_flow_status(execution_id)
        
        return FlowStatusResponse(
            execution_id=execution_id,
            status=status.get("status", "unknown"),
            result=status.get("result"),
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting flow status {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/crm/search", response_model=CRMSearchResponse)
async def search_crm_records(
    request: CRMSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search CRM records by criteria"""
    try:
        logger.info(f"Searching CRM module {request.module} with criteria: {request.criteria}")
        
        records = await zoho_client.search_crm_records(
            module=request.module,
            criteria=request.criteria,
            fields=request.fields,
            page=request.page,
            per_page=request.per_page
        )
        
        return CRMSearchResponse(
            module=request.module,
            records=records.get("data", []),
            total_count=records.get("info", {}).get("count", 0),
            page=request.page,
            per_page=request.per_page
        )
        
    except Exception as e:
        logger.error(f"Error searching CRM {request.module}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/crm/upsert", response_model=CRMUpsertResponse)
async def upsert_crm_record(
    request: CRMUpsertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create or update CRM record"""
    try:
        logger.info(f"Upserting CRM record in module {request.module}")
        
        result = await zoho_client.upsert_crm_record(
            module=request.module,
            record_data=request.record_data,
            duplicate_check_fields=request.duplicate_check_fields
        )
        
        return CRMUpsertResponse(
            module=request.module,
            record_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            operation=result.get("data", [{}])[0].get("code", "unknown"),
            details=result
        )
        
    except Exception as e:
        logger.error(f"Error upserting CRM record: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/crm/notes/create", response_model=NotesCreateResponse)
async def create_crm_note(
    request: NotesCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a note in CRM"""
    try:
        logger.info(f"Creating note for record {request.record_id} in module {request.module}")
        
        result = await zoho_client.create_crm_note(
            module=request.module,
            record_id=request.record_id,
            note_title=request.note_title,
            note_content=request.note_content
        )
        
        return NotesCreateResponse(
            note_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            record_id=request.record_id,
            module=request.module
        )
        
    except Exception as e:
        logger.error(f"Error creating CRM note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/crm/tasks/create", response_model=TasksCreateResponse)
async def create_crm_task(
    request: TasksCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a task in CRM"""
    try:
        logger.info(f"Creating task for record {request.related_record_id}")
        
        result = await zoho_client.create_crm_task(
            task_data=request.task_data,
            related_module=request.related_module,
            related_record_id=request.related_record_id
        )
        
        return TasksCreateResponse(
            task_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            related_record_id=request.related_record_id,
            related_module=request.related_module
        )
        
    except Exception as e:
        logger.error(f"Error creating CRM task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/blueprint/transition", response_model=BlueprintTransitionResponse)
async def transition_blueprint(
    request: BlueprintTransitionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute blueprint transition in CRM"""
    try:
        logger.info(f"Transitioning blueprint for record {request.record_id}")
        
        result = await zoho_client.transition_blueprint(
            module=request.module,
            record_id=request.record_id,
            transition_id=request.transition_id,
            data=request.data
        )
        
        return BlueprintTransitionResponse(
            record_id=request.record_id,
            transition_id=request.transition_id,
            status="completed",
            result=result
        )
        
    except Exception as e:
        logger.error(f"Error transitioning blueprint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/files/attach", response_model=FilesAttachResponse)
async def attach_file(
    request: FilesAttachRequest,
    current_user: dict = Depends(get_current_user)
):
    """Attach file to CRM record"""
    try:
        logger.info(f"Attaching file to record {request.record_id}")
        
        result = await zoho_client.attach_file(
            module=request.module,
            record_id=request.record_id,
            file_path=request.file_path,
            file_name=request.file_name
        )
        
        return FilesAttachResponse(
            file_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            record_id=request.record_id,
            file_name=request.file_name
        )
        
    except Exception as e:
        logger.error(f"Error attaching file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all API calls for auditing"""
    start_time = datetime.utcnow()
    
    response = await call_next(request)
    
    process_time = (datetime.utcnow() - start_time).total_seconds()
    
    logger.info(f"API Call: {request.method} {request.url.path} - "
               f"Status: {response.status_code} - Duration: {process_time:.3f}s")
    
    return response

# Enhanced CRM endpoints
@app.get("/zoho/crm/{module}/{record_id}", response_model=StandardResponse)
async def get_crm_record(
    module: str,
    record_id: str,
    fields: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get specific CRM record by ID"""
    try:
        field_list = fields.split(",") if fields else None
        record = await zoho_client.get_crm_record(module, record_id, field_list)
        
        return StandardResponse(
            success=True,
            data=record,
            message=f"Retrieved {module} record {record_id}"
        )
    except Exception as e:
        logger.error(f"Error getting {module} record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zoho/crm/{module}", response_model=StandardResponse)
async def list_crm_records(
    module: str,
    fields: Optional[str] = None,
    page: int = 1,
    per_page: int = 200,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    current_user: dict = Depends(get_current_user)
):
    """List CRM records with pagination"""
    try:
        field_list = fields.split(",") if fields else None
        records = await zoho_client.get_crm_records(
            module, field_list, page, per_page, sort_by, sort_order
        )
        
        return StandardResponse(
            success=True,
            data=records,
            message=f"Retrieved {module} records"
        )
    except Exception as e:
        logger.error(f"Error listing {module} records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/zoho/crm/{module}/{record_id}", response_model=RecordResponse)
async def update_crm_record(
    module: str,
    record_id: str,
    request: CRMRecordUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update existing CRM record"""
    try:
        result = await zoho_client.update_crm_record(module, record_id, request.record_data)
        
        return RecordResponse(
            record_id=record_id,
            module=module,
            operation="update",
            details=result
        )
    except Exception as e:
        logger.error(f"Error updating {module} record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/zoho/crm/{module}/{record_id}", response_model=StandardResponse)
async def delete_crm_record(
    module: str,
    record_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete CRM record"""
    try:
        result = await zoho_client.delete_crm_record(module, record_id)
        
        return StandardResponse(
            success=True,
            data=result,
            message=f"Deleted {module} record {record_id}"
        )
    except Exception as e:
        logger.error(f"Error deleting {module} record {record_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/leads/{lead_id}/convert", response_model=StandardResponse)
async def convert_lead(
    lead_id: str,
    request: LeadConvertRequest,
    current_user: dict = Depends(get_current_user)
):
    """Convert lead to contact/account/deal"""
    try:
        result = await zoho_client.convert_lead(lead_id, request.convert_data)
        
        return StandardResponse(
            success=True,
            data=result,
            message=f"Converted lead {lead_id}"
        )
    except Exception as e:
        logger.error(f"Error converting lead {lead_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zoho/crm/{module}/{record_id}/{related_module}", response_model=StandardResponse)
async def get_related_records(
    module: str,
    record_id: str,
    related_module: str,
    fields: Optional[str] = None,
    page: int = 1,
    per_page: int = 200,
    current_user: dict = Depends(get_current_user)
):
    """Get related records for a specific record"""
    try:
        field_list = fields.split(",") if fields else None
        records = await zoho_client.get_related_records(
            module, record_id, related_module, field_list, page, per_page
        )
        
        return StandardResponse(
            success=True,
            data=records,
            message=f"Retrieved {related_module} related to {module} {record_id}"
        )
    except Exception as e:
        logger.error(f"Error getting related records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/crm/activities/create", response_model=RecordResponse)
async def create_activity(
    request: ActivityCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create activity (call, event, task) in CRM"""
    try:
        result = await zoho_client.create_activity(
            request.activity_type,
            request.activity_data,
            request.related_module,
            request.related_record_id
        )
        
        return RecordResponse(
            record_id=result.get("data", [{}])[0].get("details", {}).get("id"),
            module=request.activity_type,
            operation="create",
            details=result
        )
    except Exception as e:
        logger.error(f"Error creating activity: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/crm/{module}/bulk_read", response_model=StandardResponse)
async def bulk_read_records(
    module: str,
    request: BulkReadRequest,
    current_user: dict = Depends(get_current_user)
):
    """Bulk read multiple records by IDs"""
    try:
        result = await zoho_client.bulk_read(module, request.record_ids, request.fields)
        
        return StandardResponse(
            success=True,
            data=result,
            message=f"Bulk read {len(request.record_ids)} {module} records"
        )
    except Exception as e:
        logger.error(f"Error bulk reading {module} records: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zoho/metadata/fields/{module}", response_model=MetadataResponse)
async def get_field_metadata(
    module: str,
    current_user: dict = Depends(get_current_user)
):
    """Get field metadata for a module"""
    try:
        metadata = await zoho_client.get_field_metadata(module)
        
        return MetadataResponse(
            module=module,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error getting field metadata for {module}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/zoho/metadata/modules/{module}", response_model=MetadataResponse)
async def get_module_metadata(
    module: str,
    current_user: dict = Depends(get_current_user)
):
    """Get metadata for a specific module"""
    try:
        metadata = await zoho_client.get_module_metadata(module)
        
        return MetadataResponse(
            module=module,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error getting module metadata for {module}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Real Estate specific endpoints
@app.post("/zoho/realty/properties/search", response_model=CRMSearchResponse)
async def search_properties(
    request: PropertySearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search properties for Impact Realty"""
    try:
        properties = await zoho_client.search_properties(
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

@app.post("/zoho/realty/agents/search", response_model=CRMSearchResponse)
async def search_agents(
    request: AgentSearchRequest,
    current_user: dict = Depends(get_current_user)
):
    """Search real estate agents"""
    try:
        agents = await zoho_client.search_agents(
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

@app.post("/zoho/realty/commissions/create", response_model=RecordResponse)
async def create_commission_record(
    request: CommissionCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create commission record for agent"""
    try:
        result = await zoho_client.create_commission_record(
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

# Webhook and notification endpoints
@app.post("/zoho/webhooks/create", response_model=StandardResponse)
async def create_webhook(
    request: WebhookCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create webhook in Zoho CRM"""
    try:
        result = await zoho_client.create_webhook(request.webhook_data)
        
        return StandardResponse(
            success=True,
            data=result,
            message="Webhook created successfully"
        )
    except Exception as e:
        logger.error(f"Error creating webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/zoho/email/send", response_model=StandardResponse)
async def send_email(
    request: EmailSendRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send email using Zoho CRM templates"""
    try:
        result = await zoho_client.send_email(
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)