#!/usr/bin/env python3
"""
Zoho MCP Server - Production FastAPI Server
Handles all Zoho CRM operations via MCP endpoints for LangFlow integration
Rick said no half-measures. This is complete and ready to run.
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
import uvicorn
import ssl
import html
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mcp_audit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Security configuration
security = HTTPBearer()
MCP_API_KEY = os.getenv('MCP_API_KEY', 'dev-mcp-key-change-in-production')

def verify_mcp_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify MCP client authentication"""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authentication")

    # In production, validate against proper key store or JWT
    if credentials.credentials != MCP_API_KEY:
        logger.warning(f"Invalid MCP authentication attempt from client")
        raise HTTPException(status_code=401, detail="Invalid authentication")

    return True

# FastAPI app with security
app = FastAPI(
    title="Zoho MCP Server",
    description="Secure production-grade MCP server for Zoho CRM integration with LangFlow",
    version="1.0.0"
)

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,https://langflow.org').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Global token storage
_access_token = None
_token_expires_at = None

# Zoho configuration
ZOHO_CONFIG = {
    'client_id': os.getenv('ZOHO_CLIENT_ID'),
    'client_secret': os.getenv('ZOHO_CLIENT_SECRET'),
    'refresh_token': os.getenv('ZOHO_REFRESH_TOKEN'),
    'base_url': os.getenv('ZOHO_CRM_BASE_URL', 'https://www.zohoapis.com/crm/v2'),
    'auth_url': os.getenv('ZOHO_AUTH_URL', 'https://accounts.zoho.com/oauth/v2/token')
}

# Input sanitization helper
def sanitize_string(value: str) -> str:
    """Sanitize string input to prevent XSS and injection"""
    if not isinstance(value, str):
        return str(value)

    # HTML escape
    value = html.escape(value)

    # Remove potentially dangerous patterns
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'\\x[0-9a-fA-F]{2}',
        r'\\u[0-9a-fA-F]{4}',
        r'eval\s*\(',
        r'exec\s*\(',
        r'__import__'
    ]

    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)

    # Remove control characters but keep newlines and tabs
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\t\r')

    return value.strip()

# Pydantic Models with enhanced validation
class ContactCreateRequest(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    phone: str = Field(..., min_length=10, max_length=15)
    source: Optional[str] = Field("LangFlow Agent", max_length=200)
    company: Optional[str] = Field(None, max_length=200)

    @validator('first_name', 'last_name', 'source', 'company', pre=True)
    def sanitize_text_fields(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

    @validator('phone', pre=True)
    def sanitize_phone(cls, v):
        if v is not None:
            # Remove all non-digits except +
            cleaned = re.sub(r'[^\d+]', '', str(v))
            if len(cleaned) < 10:
                raise ValueError('Phone number too short')
            return cleaned
        return v

    @validator('email', pre=True)
    def sanitize_email(cls, v):
        if v is not None:
            return sanitize_string(v).lower()
        return v

class DealCreateRequest(BaseModel):
    deal_name: str = Field(..., min_length=1, max_length=100)
    contact_id: str = Field(..., min_length=1)
    stage: str = Field("Qualification", max_length=50)
    amount: Optional[float] = Field(None, gt=0)
    closing_date: Optional[str] = Field(None)

    @validator('deal_name', 'stage', pre=True)
    def sanitize_text_fields(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

    @validator('contact_id', 'closing_date', pre=True)
    def sanitize_ids_dates(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

class NoteCreateRequest(BaseModel):
    contact_id: str = Field(..., min_length=1)
    note: str = Field(..., min_length=1, max_length=5000)

    @validator('contact_id', 'note', pre=True)
    def sanitize_fields(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

class TaskCreateRequest(BaseModel):
    subject: str = Field(..., min_length=1, max_length=200)
    contact_id: Optional[str] = Field(None)
    due_date: Optional[str] = Field(None)
    status: str = Field("Not Started", max_length=50)
    priority: str = Field("Normal", max_length=20)

    @validator('subject', 'contact_id', 'due_date', 'status', 'priority', pre=True)
    def sanitize_fields(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

class LeadConvertRequest(BaseModel):
    lead_id: str = Field(..., min_length=1)
    convert_to: str = Field("Contact", pattern=r'^(Contact|Deal|Account)$')

    @validator('lead_id', 'convert_to', pre=True)
    def sanitize_fields(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

class DedupeRequest(BaseModel):
    email: Optional[str] = Field(None)
    phone: Optional[str] = Field(None)
    first_name: Optional[str] = Field(None)
    last_name: Optional[str] = Field(None)

    @validator('email', pre=True)
    def sanitize_email(cls, v):
        if v is not None:
            return sanitize_string(v).lower()
        return v

    @validator('phone', pre=True)
    def sanitize_phone(cls, v):
        if v is not None:
            return re.sub(r'[^\d+]', '', str(v))
        return v

    @validator('first_name', 'last_name', pre=True)
    def sanitize_names(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

class CalendarScheduleRequest(BaseModel):
    contact_id: str = Field(..., min_length=1)
    event_title: str = Field(..., min_length=1, max_length=200)
    start_time: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$')
    end_time: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$')
    description: Optional[str] = Field(None, max_length=1000)

    @validator('contact_id', 'event_title', 'description', pre=True)
    def sanitize_text_fields(cls, v):
        if v is not None:
            return sanitize_string(v)
        return v

    @validator('start_time', 'end_time', pre=True)
    def validate_datetime_format(cls, v):
        if v is not None:
            # Ensure datetime format is valid and sanitized
            sanitized = sanitize_string(v)
            # Additional check for valid datetime format
            import datetime
            try:
                datetime.datetime.fromisoformat(sanitized)
                return sanitized
            except ValueError:
                raise ValueError('Invalid datetime format. Use YYYY-MM-DDTHH:MM:SS')
        return v

class StandardResponse(BaseModel):
    status: str
    zoho_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None

def get_valid_token() -> str:
    """
    Get a valid access token, refreshing if necessary
    """
    global _access_token, _token_expires_at

    # Check if we have a valid token
    if _access_token and _token_expires_at and datetime.now() < _token_expires_at:
        return _access_token

    logger.info("Refreshing Zoho access token...")

    try:
        # Prepare refresh request
        refresh_data = {
            'refresh_token': ZOHO_CONFIG['refresh_token'],
            'client_id': ZOHO_CONFIG['client_id'],
            'client_secret': ZOHO_CONFIG['client_secret'],
            'grant_type': 'refresh_token'
        }

        response = requests.post(
            ZOHO_CONFIG['auth_url'],
            data=refresh_data,
            timeout=30
        )

        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
            raise HTTPException(status_code=500, detail="Failed to refresh Zoho access token")

        token_data = response.json()

        if 'access_token' not in token_data:
            logger.error(f"No access token in response: {token_data}")
            raise HTTPException(status_code=500, detail="Invalid token response from Zoho")

        # Store new token with expiration
        _access_token = token_data['access_token']
        expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
        _token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # 5 min buffer

        logger.info("Successfully refreshed Zoho access token")
        return _access_token

    except requests.RequestException as e:
        logger.error(f"Network error during token refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token refresh network error: {str(e)}")

def make_zoho_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Make authenticated request to Zoho API
    """
    token = get_valid_token()

    headers = {
        'Authorization': f'Zoho-oauthtoken {token}',
        'Content-Type': 'application/json'
    }

    url = f"{ZOHO_CONFIG['base_url']}{endpoint}"

    try:
        logger.info(f"Making Zoho API request: {method} {url}")

        if method.upper() == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method.upper() == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        elif method.upper() == 'PUT':
            response = requests.put(url, headers=headers, json=data, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        logger.info(f"Zoho API response: {response.status_code}")

        if response.status_code not in [200, 201]:
            logger.error(f"Zoho API error: {response.status_code} - {response.text}")
            raise HTTPException(
                status_code=500,
                detail=f"Zoho API error: {response.status_code} - {response.text[:200]}"
            )

        return response.json()

    except requests.RequestException as e:
        logger.error(f"Network error calling Zoho API: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Zoho API network error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint - public"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/mcp/zoho/dedupe", response_model=StandardResponse)
async def dedupe_contact(request: DedupeRequest, auth: bool = Depends(verify_mcp_auth)):
    """
    Check for duplicate contacts based on email, phone, or name
    """
    logger.info(f"Dedupe request: {request.dict()}")

    try:
        # Build search criteria
        search_criteria = []

        if request.email:
            search_criteria.append(f"(Email:equals:{request.email})")

        if request.phone:
            # Clean phone number for search
            clean_phone = ''.join(filter(str.isdigit, request.phone))
            search_criteria.append(f"(Phone:equals:{clean_phone})")

        if request.first_name and request.last_name:
            search_criteria.append(
                f"((First_Name:equals:{request.first_name})and(Last_Name:equals:{request.last_name}))"
            )

        if not search_criteria:
            return StandardResponse(
                status="error",
                message="At least one search criteria required (email, phone, or name)"
            )

        # Search for contacts
        criteria = "or".join(search_criteria)
        endpoint = f"/Contacts/search?criteria={criteria}"

        result = make_zoho_request('GET', endpoint)

        contacts = result.get('data', [])

        return StandardResponse(
            status="success",
            message=f"Found {len(contacts)} potential duplicates",
            data={
                "duplicates_found": len(contacts),
                "contacts": contacts[:5]  # Return first 5 matches
            }
        )

    except Exception as e:
        logger.error(f"Dedupe error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Dedupe operation failed: {str(e)}")

@app.post("/mcp/zoho/contact/create", response_model=StandardResponse)
async def create_contact(request: ContactCreateRequest, auth: bool = Depends(verify_mcp_auth)):
    """
    Create a new contact in Zoho CRM
    """
    logger.info(f"Create contact request: {request.first_name} {request.last_name}")

    try:
        contact_data = {
            "data": [{
                "First_Name": request.first_name,
                "Last_Name": request.last_name,
                "Email": request.email,
                "Phone": request.phone,
                "Lead_Source": request.source
            }]
        }

        if request.company:
            contact_data["data"][0]["Account_Name"] = request.company

        result = make_zoho_request('POST', '/Contacts', contact_data)

        if result.get('data') and len(result['data']) > 0:
            contact_id = result['data'][0]['details']['id']
            return StandardResponse(
                status="success",
                zoho_id=contact_id,
                message="Contact created successfully",
                data=result['data'][0]
            )
        else:
            return StandardResponse(
                status="error",
                message="Failed to create contact - no data returned"
            )

    except Exception as e:
        logger.error(f"Create contact error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create contact: {str(e)}")

@app.post("/mcp/zoho/deal/create", response_model=StandardResponse)
async def create_deal(request: DealCreateRequest, auth: bool = Depends(verify_mcp_auth)):
    """
    Create a new deal in Zoho CRM
    """
    logger.info(f"Create deal request: {request.deal_name}")

    try:
        deal_data = {
            "data": [{
                "Deal_Name": request.deal_name,
                "Stage": request.stage,
                "Contact_Name": request.contact_id
            }]
        }

        if request.amount:
            deal_data["data"][0]["Amount"] = request.amount

        if request.closing_date:
            deal_data["data"][0]["Closing_Date"] = request.closing_date

        result = make_zoho_request('POST', '/Deals', deal_data)

        if result.get('data') and len(result['data']) > 0:
            deal_id = result['data'][0]['details']['id']
            return StandardResponse(
                status="success",
                zoho_id=deal_id,
                message="Deal created successfully",
                data=result['data'][0]
            )
        else:
            return StandardResponse(
                status="error",
                message="Failed to create deal - no data returned"
            )

    except Exception as e:
        logger.error(f"Create deal error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create deal: {str(e)}")

@app.post("/mcp/zoho/note/create", response_model=StandardResponse)
async def create_note(request: NoteCreateRequest, auth: bool = Depends(verify_mcp_auth)):
    """
    Create a note for a contact in Zoho CRM
    """
    logger.info(f"Create note request for contact: {request.contact_id}")

    try:
        note_data = {
            "data": [{
                "Note_Title": "Agent Interaction",
                "Note_Content": request.note,
                "Parent_Id": request.contact_id,
                "se_module": "Contacts"
            }]
        }

        result = make_zoho_request('POST', '/Notes', note_data)

        if result.get('data') and len(result['data']) > 0:
            note_id = result['data'][0]['details']['id']
            return StandardResponse(
                status="success",
                zoho_id=note_id,
                message="Note created successfully",
                data=result['data'][0]
            )
        else:
            return StandardResponse(
                status="error",
                message="Failed to create note - no data returned"
            )

    except Exception as e:
        logger.error(f"Create note error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create note: {str(e)}")

@app.post("/mcp/zoho/task/create", response_model=StandardResponse)
async def create_task(request: TaskCreateRequest, auth: bool = Depends(verify_mcp_auth)):
    """
    Create a task in Zoho CRM
    """
    logger.info(f"Create task request: {request.subject}")

    try:
        task_data = {
            "data": [{
                "Subject": request.subject,
                "Status": request.status,
                "Priority": request.priority
            }]
        }

        if request.contact_id:
            task_data["data"][0]["What_Id"] = request.contact_id

        if request.due_date:
            task_data["data"][0]["Due_Date"] = request.due_date

        result = make_zoho_request('POST', '/Tasks', task_data)

        if result.get('data') and len(result['data']) > 0:
            task_id = result['data'][0]['details']['id']
            return StandardResponse(
                status="success",
                zoho_id=task_id,
                message="Task created successfully",
                data=result['data'][0]
            )
        else:
            return StandardResponse(
                status="error",
                message="Failed to create task - no data returned"
            )

    except Exception as e:
        logger.error(f"Create task error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create task: {str(e)}")

@app.post("/mcp/zoho/lead/convert", response_model=StandardResponse)
async def convert_lead(request: LeadConvertRequest, auth: bool = Depends(verify_mcp_auth)):
    """
    Convert a lead to contact/deal in Zoho CRM
    """
    logger.info(f"Convert lead request: {request.lead_id} to {request.convert_to}")

    try:
        convert_data = {
            "data": [{
                "overwrite": True,
                "notify_lead_owner": True,
                "notify_new_entity_owner": True,
                "Accounts": "create",
                "Contacts": "create",
                "Deals": "create" if request.convert_to == "Deal" else "do_not_create"
            }]
        }

        endpoint = f"/Leads/{request.lead_id}/actions/convert"
        result = make_zoho_request('POST', endpoint, convert_data)

        if result.get('data') and len(result['data']) > 0:
            conversion_data = result['data'][0]
            return StandardResponse(
                status="success",
                zoho_id=request.lead_id,
                message=f"Lead converted to {request.convert_to} successfully",
                data=conversion_data
            )
        else:
            return StandardResponse(
                status="error",
                message="Failed to convert lead - no data returned"
            )

    except Exception as e:
        logger.error(f"Convert lead error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to convert lead: {str(e)}")

@app.post("/mcp/zoho/calendar/schedule", response_model=StandardResponse)
async def schedule_event(request: CalendarScheduleRequest, auth: bool = Depends(verify_mcp_auth)):
    """
    Schedule a calendar event in Zoho CRM
    """
    logger.info(f"Schedule event request: {request.event_title}")

    try:
        event_data = {
            "data": [{
                "Event_Title": request.event_title,
                "Start_DateTime": request.start_time,
                "End_DateTime": request.end_time,
                "What_Id": request.contact_id,
                "Event_Status": "Planned"
            }]
        }

        if request.description:
            event_data["data"][0]["Description"] = request.description

        result = make_zoho_request('POST', '/Events', event_data)

        if result.get('data') and len(result['data']) > 0:
            event_id = result['data'][0]['details']['id']
            return StandardResponse(
                status="success",
                zoho_id=event_id,
                message="Event scheduled successfully",
                data=result['data'][0]
            )
        else:
            return StandardResponse(
                status="error",
                message="Failed to schedule event - no data returned"
            )

    except Exception as e:
        logger.error(f"Schedule event error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule event: {str(e)}")

if __name__ == "__main__":
    # Validate configuration
    required_vars = ['ZOHO_CLIENT_ID', 'ZOHO_CLIENT_SECRET', 'ZOHO_REFRESH_TOKEN']
    missing_vars = [var for var in required_vars if not ZOHO_CONFIG.get(var.lower()) or ZOHO_CONFIG.get(var.lower()) == 'Generate-from-OAuth']

    if missing_vars:
        logger.warning(f"Missing or placeholder values for: {missing_vars}")
        logger.warning("Server starting in test mode - Zoho API calls will fail but MCP endpoints will be available")

    # Configure TLS/SSL for production
    ssl_cert_path = os.getenv('SSL_CERT_PATH')
    ssl_key_path = os.getenv('SSL_KEY_PATH')
    port = int(os.getenv('MCP_SERVER_PORT', '3002'))

    logger.info("All 7 secure endpoints ready: dedupe, contact/create, deal/create, note/create, task/create, lead/convert, calendar/schedule")

    if ssl_cert_path and ssl_key_path and os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
        logger.info(f"Starting secure Zoho MCP Server with TLS on port {port}...")
        uvicorn.run(
            "zoho_mcp_server:app",
            host="0.0.0.0",
            port=port,
            ssl_keyfile=ssl_key_path,
            ssl_certfile=ssl_cert_path,
            ssl_version=ssl.PROTOCOL_TLS,
            ssl_cert_reqs=ssl.CERT_NONE,  # For development, in production use CERT_REQUIRED
            reload=False,
            log_level="info",
            access_log=True
        )
    else:
        logger.info(f"Starting Zoho MCP Server (HTTP) on port {port}...")
        logger.warning("Running in HTTP mode - for production, configure SSL_CERT_PATH and SSL_KEY_PATH")
        uvicorn.run(
            "zoho_mcp_server:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )