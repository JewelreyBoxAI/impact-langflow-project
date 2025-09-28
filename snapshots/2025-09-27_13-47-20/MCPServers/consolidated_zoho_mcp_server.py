#!/usr/bin/env python3
"""
Consolidated Zoho MCP Server - Production-Ready Implementation
Combines FastAPI REST endpoints with MCP protocol support for complete Zoho CRM integration
Enhanced with file upload capabilities, robust error handling, and production features
"""

import logging
import os
import time
import json
import asyncio
import aiofiles
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

import requests
import aiohttp
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn
import ssl
import html
import re

# Load environment variables
load_dotenv()

# Import standardized configuration
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from backend.core.config_manager import get_config, get_zoho_config, get_mcp_config, setup_logging
    from backend.core.error_handler import (
        get_error_handler, get_performance_monitor, retry_with_backoff, circuit_breaker,
        ErrorSeverity, ErrorCategory, ErrorContext
    )
    from backend.core.production_readiness import (
        initialize_production_features, get_production_status, cleanup_production_features,
        performance_tracking, resource_monitor, cache_manager, connection_pool, health_checker
    )

    # Setup logging from configuration
    setup_logging()
    logger = logging.getLogger(__name__)

    # Get enhanced error handling
    error_handler = get_error_handler()
    performance_monitor = get_performance_monitor()

    # Get configurations
    app_config = get_config()
    zoho_config = get_zoho_config()
    mcp_config = get_mcp_config()

    logger.info("Using standardized configuration management with enhanced error handling")

    # Initialize production features
    production_ready = initialize_production_features()
    if production_ready:
        logger.info("Production readiness features activated")
    else:
        logger.warning("Production readiness features initialization failed")
except ImportError as e:
    # Fallback to environment variables
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('zoho_mcp_consolidated.log'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.warning(f"Standardized config not available, using fallback: {e}")

    # Create fallback config objects
    class FallbackConfig:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

    zoho_config = FallbackConfig(
        client_id=os.getenv('ZOHO_CLIENT_ID'),
        client_secret=os.getenv('ZOHO_CLIENT_SECRET'),
        refresh_token=os.getenv('ZOHO_REFRESH_TOKEN'),
        crm_base_url=os.getenv('ZOHO_CRM_BASE_URL', 'https://www.zohoapis.com/crm/v2'),
        auth_url=os.getenv('ZOHO_AUTH_URL', 'https://accounts.zoho.com/oauth/v2/token')
    )

    mcp_config = FallbackConfig(
        api_key=os.getenv('MCP_API_KEY', 'dev-mcp-key-change-in-production'),
        cors_origins=os.getenv('ALLOWED_ORIGINS', 'http://localhost:3000,https://langflow.org').split(','),
        port=int(os.getenv('MCP_SERVER_PORT', '3002')),
        upload_dir=os.getenv('UPLOAD_DIR', './uploads'),
        max_file_size=int(os.getenv('MAX_FILE_SIZE', 50 * 1024 * 1024)),
        ssl_cert_path=os.getenv('SSL_CERT_PATH'),
        ssl_key_path=os.getenv('SSL_KEY_PATH')
    )

# Security configuration
security = HTTPBearer()

def verify_mcp_auth(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify MCP client authentication"""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing authentication")

    if credentials.credentials != mcp_config.api_key:
        logger.warning("Invalid MCP authentication attempt")
        raise HTTPException(status_code=401, detail="Invalid authentication")

    return True

# FastAPI app with enhanced configuration
app = FastAPI(
    title="Consolidated Zoho MCP Server",
    description="Production-grade MCP server for comprehensive Zoho CRM integration with file upload capabilities",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=mcp_config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Token management
TOKEN_FILE = Path(__file__).parent / ".tokens.json"
_access_token = None
_token_expires_at = None
_refresh_token = None

# File upload configuration from standardized config
UPLOAD_DIR = Path(mcp_config.upload_dir)
UPLOAD_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = mcp_config.max_file_size
ALLOWED_EXTENSIONS = set(mcp_config.allowed_extensions)

def sanitize_string(value: str) -> str:
    """Enhanced string sanitization"""
    if not isinstance(value, str):
        return str(value)

    # HTML escape
    value = html.escape(value)

    # Remove dangerous patterns
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

# Enhanced Pydantic Models
class FileUploadRequest(BaseModel):
    module_name: str = Field(..., description="Zoho module to attach file to")
    record_id: str = Field(..., description="Record ID to attach file to")
    file_description: Optional[str] = Field(None, description="Description of the file")

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

class StandardResponse(BaseModel):
    status: str
    zoho_id: Optional[str] = None
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

class FileUploadResponse(BaseModel):
    file_id: str
    zoho_attachment_id: Optional[str] = None
    filename: str
    size: int
    content_type: str
    status: str
    message: str
    uploaded_at: str

# Token Management Functions
def load_tokens():
    """Load tokens from persistent storage"""
    global _access_token, _refresh_token, _token_expires_at

    try:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                _access_token = tokens.get('access_token')
                _refresh_token = tokens.get('refresh_token')
                created_at = tokens.get('created_at', 0)
                expires_in = tokens.get('expires_in', 3600)
                _token_expires_at = datetime.fromtimestamp(created_at + expires_in - 300)
                return True
    except Exception as e:
        logger.error(f"Failed to load tokens: {e}")

    # Fallback to environment variables
    if zoho_config.refresh_token and zoho_config.refresh_token != "Generate-from-OAuth":
        _refresh_token = zoho_config.refresh_token

    return _access_token is not None

def save_tokens(access_token=None, refresh_token=None, expires_in=None):
    """Save tokens to persistent storage"""
    global _access_token, _refresh_token

    if access_token:
        _access_token = access_token
    if refresh_token:
        _refresh_token = refresh_token

    token_data = {
        "access_token": _access_token,
        "refresh_token": _refresh_token,
        "created_at": int(time.time()),
        "expires_in": expires_in or 3600
    }

    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        logger.info("Tokens saved successfully")
    except Exception as e:
        logger.error(f"Failed to save tokens: {e}")

async def get_valid_token() -> str:
    """Get a valid access token, refreshing if necessary"""
    global _access_token, _token_expires_at

    # Check if we have a valid token
    if _access_token and _token_expires_at and datetime.now() < _token_expires_at:
        return _access_token

    logger.info("Refreshing Zoho access token...")

    if not _refresh_token:
        raise HTTPException(status_code=500, detail="No refresh token available")

    try:
        refresh_data = {
            'refresh_token': _refresh_token,
            'client_id': zoho_config.client_id,
            'client_secret': zoho_config.client_secret,
            'grant_type': 'refresh_token'
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(zoho_config.auth_url, data=refresh_data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"Token refresh failed: {response.status} - {error_text}")
                    raise HTTPException(status_code=500, detail="Failed to refresh Zoho access token")

                token_data = await response.json()

                if 'access_token' not in token_data:
                    logger.error(f"No access token in response: {token_data}")
                    raise HTTPException(status_code=500, detail="Invalid token response from Zoho")

                # Store new token with expiration
                _access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                _token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)

                save_tokens(access_token=_access_token, expires_in=expires_in)
                logger.info("Successfully refreshed Zoho access token")
                return _access_token

    except Exception as e:
        logger.error(f"Error during token refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token refresh error: {str(e)}")

@circuit_breaker(failure_threshold=5, recovery_timeout=60)
@retry_with_backoff(max_retries=3, exceptions=(aiohttp.ClientError, asyncio.TimeoutError))
async def make_zoho_request(method: str, endpoint: str, data: Dict[str, Any] = None, files: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make authenticated request to Zoho API with enhanced error handling and circuit breaker"""

    # Create error context
    context = ErrorContext(
        component="zoho_api_client",
        operation=f"{method}_{endpoint}",
        metadata={
            "method": method,
            "endpoint": endpoint,
            "has_files": files is not None,
            "has_data": data is not None
        }
    )

    with performance_monitor.measure_time(f"zoho_api_{method.lower()}"):
        try:
            token = await get_valid_token()

            headers = {
                'Authorization': f'Zoho-oauthtoken {token}'
            }

            # Don't set Content-Type for file uploads - let aiohttp handle it
            if not files:
                headers['Content-Type'] = 'application/json'

            url = f"{zoho_config.crm_base_url}{endpoint}"

            logger.info(f"Making Zoho API request: {method} {url}")

            # Set timeout for requests
            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                if method.upper() == 'GET':
                    async with session.get(url, headers=headers) as response:
                        result = await response.json()
                elif method.upper() == 'POST':
                    if files:
                        # Handle file upload
                        async with session.post(url, headers=headers, data=files) as response:
                            result = await response.json()
                    else:
                        async with session.post(url, headers=headers, json=data) as response:
                            result = await response.json()
                elif method.upper() == 'PUT':
                    async with session.put(url, headers=headers, json=data) as response:
                        result = await response.json()
                else:
                    error_handler.log_error(
                        f"Unsupported HTTP method: {method}",
                        ErrorSeverity.HIGH,
                        ErrorCategory.VALIDATION,
                        context
                    )
                    raise ValueError(f"Unsupported HTTP method: {method}")

                logger.info(f"Zoho API response: {response.status}")

                # Handle different response codes
                if response.status == 401:
                    error_handler.log_error(
                        "Zoho API authentication failed",
                        ErrorSeverity.HIGH,
                        ErrorCategory.AUTHENTICATION,
                        context
                    )
                    raise HTTPException(status_code=401, detail="Zoho API authentication failed")

                elif response.status == 403:
                    error_handler.log_error(
                        "Zoho API authorization failed",
                        ErrorSeverity.HIGH,
                        ErrorCategory.AUTHORIZATION,
                        context
                    )
                    raise HTTPException(status_code=403, detail="Zoho API authorization failed")

                elif response.status == 429:
                    error_handler.log_error(
                        "Zoho API rate limit exceeded",
                        ErrorSeverity.MEDIUM,
                        ErrorCategory.RATE_LIMIT,
                        context
                    )
                    raise HTTPException(status_code=429, detail="Zoho API rate limit exceeded")

                elif response.status not in [200, 201]:
                    error_handler.log_error(
                        f"Zoho API error: {response.status}",
                        ErrorSeverity.HIGH,
                        ErrorCategory.INTEGRATION,
                        context,
                        details=str(result)[:500]
                    )
                    raise HTTPException(
                        status_code=500,
                        detail=f"Zoho API error: {response.status} - {str(result)[:200]}"
                    )

                # Log successful API call
                error_handler.log_success(
                    f"Zoho API call successful: {method} {endpoint}",
                    context,
                    {"response_status": response.status}
                )

                return result

        except HTTPException:
            # Re-raise HTTP exceptions without additional logging
            raise
        except asyncio.TimeoutError as e:
            error_handler.log_error(
                f"Zoho API timeout: {str(e)}",
                ErrorSeverity.HIGH,
                ErrorCategory.TIMEOUT,
                context,
                e
            )
            raise HTTPException(status_code=504, detail="Zoho API request timeout")
        except aiohttp.ClientError as e:
            error_handler.log_error(
                f"Zoho API client error: {str(e)}",
                ErrorSeverity.HIGH,
                ErrorCategory.NETWORK,
                context,
                e
            )
            raise HTTPException(status_code=500, detail=f"Zoho API network error: {str(e)}")
        except Exception as e:
            error_handler.log_error(
                f"Unexpected error in Zoho API call: {str(e)}",
                ErrorSeverity.CRITICAL,
                ErrorCategory.UNKNOWN,
                context,
                e
            )
            raise HTTPException(status_code=500, detail=f"Zoho API unexpected error: {str(e)}")

# File Upload Helper Functions
async def save_uploaded_file(file: UploadFile) -> Dict[str, Any]:
    """Save uploaded file and return metadata"""
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Generate unique filename
    timestamp = int(time.time())
    safe_filename = f"{timestamp}_{sanitize_string(file.filename)}"
    file_path = UPLOAD_DIR / safe_filename

    # Read and validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File size {len(content)} exceeds maximum allowed size {MAX_FILE_SIZE}"
        )

    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(content)

    return {
        'file_path': str(file_path),
        'filename': file.filename,
        'safe_filename': safe_filename,
        'size': len(content),
        'content_type': file.content_type
    }

# API Endpoints

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "services": {
            "zoho_api": "available" if _access_token else "token_required",
            "file_upload": "enabled",
            "mcp_protocol": "enabled"
        }
    }

@app.post("/mcp/zoho/file/upload", response_model=FileUploadResponse)
@performance_tracking("file_upload")
@retry_with_backoff(max_retries=2, exceptions=(aiohttp.ClientError, OSError))
async def upload_file_to_zoho(
    file: UploadFile = File(...),
    module_name: str = Form(...),
    record_id: str = Form(...),
    file_description: Optional[str] = Form(None),
    auth: bool = Depends(verify_mcp_auth)
):
    """
    Upload file and attach to Zoho CRM record - COMPLETE IMPLEMENTATION WITH ENHANCED ERROR HANDLING
    """
    # Create error context
    context = ErrorContext(
        component="mcp_server",
        operation="file_upload",
        metadata={
            "module_name": module_name,
            "record_id": record_id,
            "filename": file.filename,
            "content_type": file.content_type
        }
    )

    logger.info(f"File upload request: {file.filename} to {module_name}/{record_id}")

    # Measure performance
    with performance_monitor.measure_time("file_upload_total"):
        try:
            # Validate inputs
            if not file.filename:
                error_handler.log_error(
                    "File upload failed: No filename provided",
                    ErrorSeverity.MEDIUM,
                    ErrorCategory.VALIDATION,
                    context
                )
                raise HTTPException(status_code=400, detail="Filename is required")

            # Save file locally first
            with performance_monitor.measure_time("file_save_local"):
                file_metadata = await save_uploaded_file(file)

            # Prepare file for Zoho upload
            with performance_monitor.measure_time("file_prepare_upload"):
                file_content = open(file_metadata['file_path'], 'rb').read()

                # Create multipart form data for Zoho API
                files_data = {
                    'file': (file_metadata['filename'], file_content, file.content_type),
                    'type': 'attachment'
                }

            # Upload to Zoho CRM
            with performance_monitor.measure_time("zoho_api_upload"):
                endpoint = f"/{module_name}/{record_id}/Attachments"
                result = await make_zoho_request('POST', endpoint, files=files_data)

            # Clean up local file after successful upload
            try:
                os.unlink(file_metadata['file_path'])
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up local file: {cleanup_error}")

            # Extract Zoho attachment ID
            zoho_attachment_id = None
            if result.get('data') and len(result['data']) > 0:
                zoho_attachment_id = result['data'][0].get('details', {}).get('id')

            # Log success
            error_handler.log_success(
                f"File {file.filename} uploaded successfully",
                context,
                {
                    "file_size": file_metadata['size'],
                    "zoho_attachment_id": zoho_attachment_id
                }
            )

            return FileUploadResponse(
                file_id=file_metadata['safe_filename'],
                zoho_attachment_id=zoho_attachment_id,
                filename=file_metadata['filename'],
                size=file_metadata['size'],
                content_type=file_metadata['content_type'],
                status="success",
                message="File uploaded and attached to Zoho record successfully",
                uploaded_at=datetime.utcnow().isoformat()
            )

        except HTTPException:
            # Re-raise HTTP exceptions without additional logging
            raise
        except Exception as e:
            # Enhanced error logging
            error_handler.log_error(
                f"File upload failed: {str(e)}",
                ErrorSeverity.HIGH,
                ErrorCategory.FILE_UPLOAD,
                context,
                e
            )

            # Clean up local file on error
            try:
                if 'file_metadata' in locals():
                    os.unlink(file_metadata['file_path'])
            except:
                pass

            raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.post("/mcp/zoho/contact/create", response_model=StandardResponse)
async def create_contact(request: ContactCreateRequest, auth: bool = Depends(verify_mcp_auth)):
    """Create a new contact in Zoho CRM"""
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

        result = await make_zoho_request('POST', '/Contacts', contact_data)

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

# MCP Protocol Tools Implementation
@app.post("/mcp/tools/get_module_data")
async def mcp_get_module_data(
    parameters: Dict[str, Any],
    auth: bool = Depends(verify_mcp_auth)
):
    """MCP tool: Fetch data from Zoho CRM modules"""
    module_name = parameters.get('module_name')

    try:
        if module_name:
            endpoint = f"/{module_name}"
            result = await make_zoho_request('GET', endpoint)

            data = result.get("data", [])
            return {
                "status": "success",
                "module": module_name,
                "count": len(data),
                "data": data
            }
        else:
            # Fetch from all modules
            modules = ["Leads", "Accounts", "Contacts", "Deals"]
            all_data = {}

            for module in modules:
                try:
                    endpoint = f"/{module}"
                    result = await make_zoho_request('GET', endpoint)
                    data = result.get("data", [])
                    all_data[module] = {
                        "count": len(data),
                        "data": data
                    }
                except Exception as module_error:
                    logger.warning(f"Failed to fetch {module}: {module_error}")
                    all_data[module] = {"error": str(module_error)}

            return {
                "status": "success",
                "modules_fetched": len([m for m in all_data if 'error' not in all_data[m]]),
                "total_records": sum(m.get("count", 0) for m in all_data.values() if isinstance(m, dict) and 'count' in m),
                "data": all_data
            }

    except Exception as e:
        logger.error(f"MCP get_module_data error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/mcp/tools/create_record")
async def mcp_create_record(
    parameters: Dict[str, Any],
    auth: bool = Depends(verify_mcp_auth)
):
    """MCP tool: Create a new record in a specific module"""
    module_name = parameters.get('module_name')
    record_data = parameters.get('record_data')

    if not module_name or not record_data:
        return {"status": "error", "message": "module_name and record_data are required"}

    try:
        endpoint = f"/{module_name}"
        payload = {"data": [record_data]}
        result = await make_zoho_request('POST', endpoint, payload)

        if result.get('data') and len(result['data']) > 0:
            return {
                "status": "success",
                "module": module_name,
                "message": "Record created successfully",
                "data": result['data'][0]
            }
        else:
            return {
                "status": "error",
                "module": module_name,
                "message": "Failed to create record - no data returned"
            }

    except Exception as e:
        logger.error(f"MCP create_record error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.post("/mcp/tools/search_records")
async def mcp_search_records(
    parameters: Dict[str, Any],
    auth: bool = Depends(verify_mcp_auth)
):
    """MCP tool: Search for records in a specific module"""
    module_name = parameters.get('module_name')
    search_criteria = parameters.get('search_criteria')

    if not module_name or not search_criteria:
        return {"status": "error", "message": "module_name and search_criteria are required"}

    try:
        endpoint = f"/{module_name}/search?criteria={search_criteria}"
        result = await make_zoho_request('GET', endpoint)

        data = result.get("data", [])
        return {
            "status": "success",
            "module": module_name,
            "count": len(data),
            "data": data
        }

    except Exception as e:
        logger.error(f"MCP search_records error: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/mcp/tools/list")
async def list_mcp_tools():
    """List all available MCP tools"""
    return {
        "tools": [
            {"name": "get_module_data", "description": "Fetch data from Zoho CRM modules"},
            {"name": "create_record", "description": "Create a new record in a specific module"},
            {"name": "search_records", "description": "Search for records in a specific module"},
            {"name": "upload_file", "description": "Upload file and attach to Zoho CRM record"},
            {"name": "get_token_status", "description": "Get current OAuth token status"},
            {"name": "test_connection", "description": "Test Zoho API connection"}
        ]
    }

@app.get("/mcp/status")
async def mcp_status():
    """Get comprehensive MCP server status with error and performance metrics"""
    try:
        # Get error statistics
        error_stats = error_tracker.get_error_stats()

        # Get performance metrics
        performance_metrics = performance_monitor.get_metrics_summary()

        return {
            "server_status": "running",
            "version": "2.0.0",
            "zoho_connection": "authenticated" if _access_token else "not_authenticated",
            "features": {
                "file_upload": True,
                "mcp_protocol": True,
                "oauth_management": True,
                "rest_api": True,
                "enhanced_error_handling": True,
                "performance_monitoring": True,
                "circuit_breaker": True
            },
            "health": {
                "errors_24h": error_stats.get('total_errors', 0),
                "critical_errors_24h": error_stats.get('by_severity', {}).get('critical', 0),
                "resolved_errors_24h": error_stats.get('resolved_count', 0),
                "performance_metrics": performance_metrics
            },
            "uptime": time.time(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        # Fallback status if error tracking fails
        logger.warning(f"Failed to get enhanced status: {e}")
        return {
            "server_status": "running",
            "version": "2.0.0",
            "zoho_connection": "authenticated" if _access_token else "not_authenticated",
            "error": "Enhanced status unavailable",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/mcp/health/errors")
async def get_error_statistics():
    """Get detailed error statistics"""
    try:
        return {
            "error_stats_24h": error_tracker.get_error_stats(24),
            "error_stats_7d": error_tracker.get_error_stats(24 * 7),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get error statistics: {str(e)}")

@app.get("/mcp/health/performance")
async def get_performance_metrics():
    """Get detailed performance metrics"""
    try:
        return {
            "performance_summary": performance_monitor.get_metrics_summary(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get performance metrics: {str(e)}")

@app.get("/mcp/production/status")
async def get_production_status_endpoint():
    """Get comprehensive production status including resource monitoring"""
    try:
        return get_production_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get production status: {str(e)}")

@app.get("/mcp/production/health")
async def run_health_checks():
    """Run all registered health checks"""
    try:
        return await health_checker.run_all_checks()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/mcp/production/cache/stats")
async def get_cache_statistics():
    """Get cache performance statistics"""
    try:
        return {
            "cache_stats": cache_manager.get_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")

@app.post("/mcp/production/cache/clear")
async def clear_cache():
    """Clear all cache entries"""
    try:
        cache_manager.clear()
        return {
            "status": "success",
            "message": "Cache cleared successfully",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")

@app.get("/mcp/production/connections")
async def get_connection_pool_status():
    """Get connection pool status"""
    try:
        return {
            "connection_pool": connection_pool.get_pool_stats(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connection pool status: {str(e)}")

# Initialize server
async def initialize_server():
    """Initialize server with token loading"""
    logger.info("Initializing Consolidated Zoho MCP Server...")

    # Validate configuration
    required_vars = ['ZOHO_CLIENT_ID', 'ZOHO_CLIENT_SECRET']
    missing_vars = [var for var in required_vars if not ZOHO_CONFIG.get(var.lower())]

    if missing_vars:
        logger.warning(f"Missing required variables: {missing_vars}")
        logger.warning("Server starting in limited mode")
    else:
        # Try to load existing tokens
        if load_tokens():
            logger.info("✅ Tokens loaded from storage")
            try:
                # Test connection
                await get_valid_token()
                logger.info("✅ Zoho API connection verified")
            except Exception as e:
                logger.warning(f"Token validation failed: {e}")
        else:
            logger.info("⚠️ No valid tokens found - manual authentication required")

@app.on_event("startup")
async def startup_event():
    await initialize_server()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    try:
        logger.info("Server shutdown initiated - cleaning up resources")
        cleanup_production_features()
        logger.info("Server shutdown completed")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

if __name__ == "__main__":
    # Validate configuration on startup using standardized config
    missing_vars = []
    if not zoho_config.client_id or zoho_config.client_id == 'Generate-from-OAuth':
        missing_vars.append('ZOHO_CLIENT_ID')
    if not zoho_config.client_secret or zoho_config.client_secret == 'Generate-from-OAuth':
        missing_vars.append('ZOHO_CLIENT_SECRET')

    if missing_vars:
        logger.warning(f"Missing or placeholder values for: {missing_vars}")
        logger.warning("Server starting in test mode - some Zoho API calls may fail")

    # Configure TLS/SSL for production from standardized config
    ssl_cert_path = mcp_config.ssl_cert_path
    ssl_key_path = mcp_config.ssl_key_path
    port = mcp_config.port

    logger.info("🚀 Consolidated Zoho MCP Server with complete file upload support ready!")
    logger.info("Features: REST API + MCP Protocol + File Upload + OAuth Management")

    if ssl_cert_path and ssl_key_path and os.path.exists(ssl_cert_path) and os.path.exists(ssl_key_path):
        logger.info(f"Starting secure server with TLS on port {port}...")
        uvicorn.run(
            "consolidated_zoho_mcp_server:app",
            host="0.0.0.0",
            port=port,
            ssl_keyfile=ssl_key_path,
            ssl_certfile=ssl_cert_path,
            ssl_version=ssl.PROTOCOL_TLS,
            ssl_cert_reqs=ssl.CERT_NONE,
            reload=False,
            log_level="info",
            access_log=True
        )
    else:
        logger.info(f"Starting server (HTTP) on port {port}...")
        logger.warning("Running in HTTP mode - for production, configure SSL_CERT_PATH and SSL_KEY_PATH")
        uvicorn.run(
            "consolidated_zoho_mcp_server:app",
            host="0.0.0.0",
            port=port,
            reload=False,
            log_level="info",
            access_log=True
        )