"""
Pydantic models for MCP server request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

# Zoho Flow schemas
class FlowRunRequest(BaseModel):
    flow_id: str = Field(..., description="Zoho Flow ID to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Flow input parameters")

class FlowRunResponse(BaseModel):
    flow_id: str
    execution_id: Optional[str] = None
    status: str
    result: Dict[str, Any]
    timestamp: str

class FlowStatusResponse(BaseModel):
    execution_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    timestamp: str

# Zoho CRM schemas
class CRMSearchRequest(BaseModel):
    module: str = Field(..., description="CRM module name (Leads, Contacts, etc.)")
    criteria: str = Field(..., description="Search criteria in Zoho format")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    page: int = Field(1, description="Page number")
    per_page: int = Field(200, description="Records per page", le=200)

class CRMSearchResponse(BaseModel):
    module: str
    records: List[Dict[str, Any]]
    total_count: int
    page: int
    per_page: int

class CRMUpsertRequest(BaseModel):
    module: str = Field(..., description="CRM module name")
    record_data: Dict[str, Any] = Field(..., description="Record data to upsert")
    duplicate_check_fields: Optional[List[str]] = Field(None, description="Fields to check for duplicates")

class CRMUpsertResponse(BaseModel):
    module: str
    record_id: Optional[str] = None
    operation: str  # "insert" or "update"
    details: Dict[str, Any]

# Notes schemas
class NotesCreateRequest(BaseModel):
    module: str = Field(..., description="Parent record module")
    record_id: str = Field(..., description="Parent record ID")
    note_title: str = Field(..., description="Note title")
    note_content: str = Field(..., description="Note content")

class NotesCreateResponse(BaseModel):
    note_id: Optional[str] = None
    record_id: str
    module: str

# Tasks schemas
class TasksCreateRequest(BaseModel):
    task_data: Dict[str, Any] = Field(..., description="Task details")
    related_module: Optional[str] = Field(None, description="Related record module")
    related_record_id: Optional[str] = Field(None, description="Related record ID")

class TasksCreateResponse(BaseModel):
    task_id: Optional[str] = None
    related_record_id: Optional[str] = None
    related_module: Optional[str] = None

# Blueprint schemas
class BlueprintTransitionRequest(BaseModel):
    module: str = Field(..., description="CRM module name")
    record_id: str = Field(..., description="Record ID")
    transition_id: str = Field(..., description="Blueprint transition ID")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional transition data")

class BlueprintTransitionResponse(BaseModel):
    record_id: str
    transition_id: str
    status: str
    result: Dict[str, Any]

# Files schemas
class FilesAttachRequest(BaseModel):
    module: str = Field(..., description="Parent record module")
    record_id: str = Field(..., description="Parent record ID")
    file_path: str = Field(..., description="Path to file to attach")
    file_name: str = Field(..., description="Display name for file")

class FilesAttachResponse(BaseModel):
    file_id: Optional[str] = None
    record_id: str
    file_name: str

# Enhanced CRM schemas for Impact workflows
class CRMRecordGetRequest(BaseModel):
    module: str = Field(..., description="CRM module name")
    record_id: str = Field(..., description="Record ID")
    fields: Optional[List[str]] = Field(None, description="Fields to return")

class CRMRecordsListRequest(BaseModel):
    module: str = Field(..., description="CRM module name")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    page: int = Field(1, description="Page number")
    per_page: int = Field(200, description="Records per page", le=200)
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field("asc", description="Sort order (asc/desc)")

class CRMRecordUpdateRequest(BaseModel):
    module: str = Field(..., description="CRM module name")
    record_id: str = Field(..., description="Record ID")
    record_data: Dict[str, Any] = Field(..., description="Updated record data")

class CRMRecordDeleteRequest(BaseModel):
    module: str = Field(..., description="CRM module name")
    record_id: str = Field(..., description="Record ID")

class LeadConvertRequest(BaseModel):
    lead_id: str = Field(..., description="Lead ID to convert")
    convert_data: Dict[str, Any] = Field(..., description="Conversion data")

class RelatedRecordsRequest(BaseModel):
    module: str = Field(..., description="Parent module")
    record_id: str = Field(..., description="Parent record ID")
    related_module: str = Field(..., description="Related module")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    page: int = Field(1, description="Page number")
    per_page: int = Field(200, description="Records per page", le=200)

class ActivityCreateRequest(BaseModel):
    activity_type: str = Field(..., description="Activity type (Calls, Events, Tasks)")
    activity_data: Dict[str, Any] = Field(..., description="Activity details")
    related_module: Optional[str] = Field(None, description="Related module")
    related_record_id: Optional[str] = Field(None, description="Related record ID")

class BulkReadRequest(BaseModel):
    module: str = Field(..., description="CRM module name")
    record_ids: List[str] = Field(..., description="List of record IDs")
    fields: Optional[List[str]] = Field(None, description="Fields to return")

class FieldMetadataRequest(BaseModel):
    module: str = Field(..., description="Module name")

class ModuleMetadataRequest(BaseModel):
    module: str = Field(..., description="Module name")

# Real Estate specific schemas
class PropertySearchRequest(BaseModel):
    criteria: str = Field(..., description="Property search criteria")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    page: int = Field(1, description="Page number")
    per_page: int = Field(200, description="Records per page", le=200)

class AgentSearchRequest(BaseModel):
    criteria: str = Field(..., description="Agent search criteria")
    fields: Optional[List[str]] = Field(None, description="Fields to return")
    page: int = Field(1, description="Page number")
    per_page: int = Field(200, description="Records per page", le=200)

class CommissionCreateRequest(BaseModel):
    agent_id: str = Field(..., description="Agent ID")
    deal_id: str = Field(..., description="Deal ID")
    commission_amount: float = Field(..., description="Commission amount")
    commission_data: Dict[str, Any] = Field(default_factory=dict, description="Additional commission data")

# Webhook and notification schemas
class WebhookCreateRequest(BaseModel):
    webhook_data: Dict[str, Any] = Field(..., description="Webhook configuration")

class EmailSendRequest(BaseModel):
    template_id: str = Field(..., description="Email template ID")
    recipient_emails: List[str] = Field(..., description="Recipient email addresses")
    merge_data: Dict[str, Any] = Field(default_factory=dict, description="Template merge data")
    related_record_id: Optional[str] = Field(None, description="Related record ID")

# Standard response schemas
class StandardResponse(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class RecordResponse(BaseModel):
    record_id: Optional[str] = None
    module: str
    operation: str
    details: Optional[Dict[str, Any]] = None

class MetadataResponse(BaseModel):
    module: str
    metadata: Dict[str, Any]

# Error response schema
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())