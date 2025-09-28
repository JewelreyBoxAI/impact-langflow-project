"""
MCP (Model Context Protocol) Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class MCPServerStatus(BaseModel):
    server_name: str = Field(..., description="MCP server name")
    status: str = Field(..., description="Server status (online, offline, error)")
    last_ping: Optional[str] = Field(None, description="Last successful ping timestamp")
    response_time: Optional[float] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if applicable")
    uptime: Optional[int] = Field(None, description="Server uptime in seconds")

class MCPRequest(BaseModel):
    server_name: str = Field(..., description="Target MCP server name")
    method: str = Field(..., description="MCP method to call")
    params: Dict[str, Any] = Field(default_factory=dict, description="Method parameters")
    timeout: Optional[int] = Field(30, description="Request timeout in seconds")

class MCPResponse(BaseModel):
    server_name: str
    method: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    execution_time: Optional[float] = Field(None, description="Execution time in milliseconds")

class MCPDedupeRequest(BaseModel):
    prospects: List[Dict[str, Any]] = Field(..., description="Prospects to deduplicate")
    dedupe_fields: List[str] = Field(default=["email", "phone"], description="Fields for deduplication")
    strict_mode: bool = Field(False, description="Use strict matching")

class MCPDedupeResponse(BaseModel):
    unique_prospects: List[Dict[str, Any]] = Field(default_factory=list)
    duplicates: List[Dict[str, Any]] = Field(default_factory=list)
    duplicates_count: int
    unique_count: int
    processing_time: float = Field(0.0, description="Processing time in seconds")
    dedupe_summary: Optional[Dict[str, Any]] = Field(None, description="Deduplication summary")

class MCPServerConfig(BaseModel):
    server_name: str
    host: str = Field(default="localhost")
    port: int = Field(default=3001)
    protocol: str = Field(default="http")
    api_key: Optional[str] = Field(None)
    timeout: int = Field(30)
    max_retries: int = Field(3)
    enabled: bool = Field(True)