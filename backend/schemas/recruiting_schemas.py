"""
Pydantic models for recruiting workflow request/response schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional
from datetime import datetime

# Recruiting Flow schemas
class ProspectData(BaseModel):
    name: str = Field(..., description="Prospect full name")
    email: str = Field(..., description="Prospect email address")
    phone: str = Field(..., description="Prospect phone number")
    company: Optional[str] = Field(None, description="Prospect company")
    license_number: Optional[str] = Field(None, description="Real estate license number")
    license_type: Optional[str] = Field("Sales Associate", description="License type")
    additional_data: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('email')
    def validate_email(cls, v):
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        import re
        cleaned = re.sub(r'\D', '', v)
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError('Invalid phone number')
        return cleaned

class FlowConfig(BaseModel):
    enable_sms: bool = Field(True, description="Enable SMS outreach")
    enable_email: bool = Field(True, description="Enable email outreach")
    enable_calendar: bool = Field(False, description="Enable calendar scheduling")
    max_retry_attempts: int = Field(3, description="Maximum retry attempts")
    delay_between_contacts: int = Field(300, description="Delay in seconds between contacts")

class RecruitingFlowRequest(BaseModel):
    prospects: List[ProspectData] = Field(..., description="List of prospects to process")
    flow_config: FlowConfig = Field(default_factory=FlowConfig)
    user_context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class RecruitingFlowResponse(BaseModel):
    execution_id: str
    status: str
    prospects_count: int
    estimated_completion: str
    message: str

# Prospect validation schemas
class ProspectValidationRequest(BaseModel):
    prospect_data: Dict[str, Any] = Field(..., description="Raw prospect data to validate")

class ProspectValidationResponse(BaseModel):
    is_valid: bool
    validated_prospect: Optional[ProspectData] = None
    validation_errors: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

class ProspectUploadResponse(BaseModel):
    file_id: str
    total_prospects: int
    valid_prospects: int
    invalid_prospects: int
    validation_errors: List[str] = Field(default_factory=list)
    prospects: List[ProspectData] = Field(default_factory=list)

# Flow execution status schema
class FlowExecutionStatus(BaseModel):
    execution_id: str
    status: str  # "running", "completed", "failed", "paused"
    progress_percentage: int
    current_step: str
    completed_prospects: int
    failed_prospects: int
    results: Dict[str, Any] = Field(default_factory=dict)
    error_messages: List[str] = Field(default_factory=list)

# Outreach schemas
class OutreachRequest(BaseModel):
    recipient: str = Field(..., description="Recipient email or phone")
    message: str = Field(..., description="Outreach message content")
    subject: Optional[str] = Field(None, description="Email subject (for email outreach)")
    channel: str = Field(..., description="Outreach channel (sms, email, calendar)")
    prospect_data: Dict[str, Any] = Field(default_factory=dict)
    scheduling_preferences: Optional[Dict[str, Any]] = Field(None, description="Calendar preferences")

class OutreachResponse(BaseModel):
    outreach_id: str
    channel: str
    status: str
    recipient: str
    sent_at: str
    details: Dict[str, Any] = Field(default_factory=dict)

# Chat schemas
class ChatMessage(BaseModel):
    session_id: str = Field(..., description="Chat session ID")
    content: str = Field(..., description="Message content")
    sender: str = Field("User", description="Message sender")
    timestamp: Optional[str] = Field(default_factory=lambda: datetime.utcnow().isoformat())

# Analytics schemas
class ChannelPerformance(BaseModel):
    channel: str
    total_sent: int
    responses: int
    response_rate: float
    conversions: int
    conversion_rate: float

class DailyMetric(BaseModel):
    date: str
    prospects_contacted: int
    responses_received: int
    conversions: int

class RecruitingAnalytics(BaseModel):
    total_prospects: int
    successful_contacts: int
    response_rate: float
    conversion_rate: float
    channel_performance: List[ChannelPerformance] = Field(default_factory=list)
    daily_metrics: List[DailyMetric] = Field(default_factory=list)
    top_performing_messages: List[Dict[str, Any]] = Field(default_factory=list)

# MCP Integration schemas
class MCPDedupeRequest(BaseModel):
    prospects: List[ProspectData] = Field(..., description="Prospects to deduplicate")
    dedupe_fields: List[str] = Field(default=["email", "phone"], description="Fields to use for deduplication")

class MCPDedupeResponse(BaseModel):
    unique_prospects: List[ProspectData] = Field(default_factory=list)
    duplicates: List[Dict[str, Any]] = Field(default_factory=list)
    duplicates_count: int
    unique_count: int

# WebSocket message schemas
class WebSocketMessage(BaseModel):
    type: str = Field(..., description="Message type")
    content: str = Field(..., description="Message content")
    session_id: str = Field(..., description="Session ID")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

# File upload schemas
class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: str
    user_id: str

# Export schemas
class ExportRequest(BaseModel):
    format: str = Field("csv", description="Export format (csv, json, xlsx)")
    date_from: Optional[str] = Field(None, description="Start date filter")
    date_to: Optional[str] = Field(None, description="End date filter")
    include_fields: Optional[List[str]] = Field(None, description="Fields to include in export")

class ExportResponse(BaseModel):
    export_id: str
    format: str
    record_count: int
    file_size: int
    download_url: str
    expires_at: str