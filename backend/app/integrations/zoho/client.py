"""
Zoho API client with OAuth handling and retry logic
"""

import aiohttp
import aiofiles
import asyncio
import os
import json
import logging
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from urllib.parse import urlencode

# from ..azure.keyvault_client import keyvault_client

logger = logging.getLogger(__name__)

class ZohoClient:
    def __init__(self):
        self.client_id = os.getenv("ZOHO_CLIENT_ID")
        self.client_secret = os.getenv("ZOHO_CLIENT_SECRET")
        self.refresh_token = os.getenv("ZOHO_REFRESH_TOKEN")
        self.access_token = os.getenv("ZOHO_ACCESS_TOKEN")  # optional cached token
        self.token_expires_at = None

        logger.info("Initialized ZohoClient with credentials from environment variables")

        if not all([self.client_id, self.client_secret, self.refresh_token]):
            logger.warning("Missing Zoho credentials. Some functionality may not work.")

            logger.debug(f"client_id: {'✓' if self.client_id else '✗'}")
            logger.debug(f"client_secret: {'✓' if self.client_secret else '✗'}")
            logger.debug(f"refresh_token: {'✓' if self.refresh_token else '✗'}")
        
        # API endpoints
        self.auth_url = "https://accounts.zoho.com/oauth/v2/token"
        self.crm_base_url = "https://www.zohoapis.com/crm/v3"
        self.flow_base_url = "https://flow.zoho.com/api/v1"
        
        # Rate limiting
        self.max_requests_per_minute = 100
        self.request_timestamps = []
        
    async def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if (self.access_token is None or 
            self.token_expires_at is None or 
            datetime.utcnow() >= self.token_expires_at):
            await self._refresh_access_token()
    
    async def _refresh_access_token(self):
        """Refresh the access token using refresh token"""
        data = {
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.auth_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data["access_token"]
                    expires_in = token_data.get("expires_in", 3600)
                    self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    logger.info("Successfully refreshed Zoho access token")
                else:
                    error_text = await response.text()
                    logger.error(f"Failed to refresh token: {response.status} - {error_text}")
                    raise Exception(f"Token refresh failed: {error_text}")
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting"""
        now = datetime.utcnow()
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if now - ts < timedelta(minutes=1)
        ]
        
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            sleep_time = 60 - (now - self.request_timestamps[0]).total_seconds()
            if sleep_time > 0:
                logger.warning(f"Rate limit reached, sleeping {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
        
        self.request_timestamps.append(now)
    
    async def _make_request(self, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated API request with retry logic"""
        await self._ensure_valid_token()
        await self._rate_limit_check()
        
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Zoho-oauthtoken {self.access_token}"
        headers["Content-Type"] = "application/json"
        kwargs["headers"] = headers
        
        for attempt in range(3):  # 3 retry attempts
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.request(method, url, **kwargs) as response:
                        if response.status == 401:  # Token expired
                            await self._refresh_access_token()
                            headers["Authorization"] = f"Zoho-oauthtoken {self.access_token}"
                            continue
                        
                        response_text = await response.text()
                        
                        if response.status >= 400:
                            logger.error(f"API error {response.status}: {response_text}")
                            raise Exception(f"API error {response.status}: {response_text}")
                        
                        try:
                            return json.loads(response_text) if response_text else {}
                        except json.JSONDecodeError:
                            return {"raw_response": response_text}
                            
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}): {str(e)}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    # Zoho Flow methods
    async def run_flow(self, flow_id: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Zoho Flow"""
        url = f"{self.flow_base_url}/flows/{flow_id}/execute"
        return await self._make_request("POST", url, json=parameters)
    
    async def get_flow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get flow execution status"""
        url = f"{self.flow_base_url}/executions/{execution_id}"
        return await self._make_request("GET", url)
    
    # Zoho CRM methods
    async def search_crm_records(
        self,
        module: str,
        criteria: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Search CRM records"""
        params = {
            "criteria": criteria,
            "page": page,
            "per_page": per_page
        }
        if fields:
            params["fields"] = ",".join(fields)
        
        url = f"{self.crm_base_url}/{module}/search?" + urlencode(params)
        return await self._make_request("GET", url)
    
    async def upsert_crm_record(
        self,
        module: str,
        record_data: Dict[str, Any],
        duplicate_check_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create or update CRM record"""
        url = f"{self.crm_base_url}/{module}/upsert"
        
        data = {"data": [record_data]}
        if duplicate_check_fields:
            data["duplicate_check_fields"] = duplicate_check_fields
        
        return await self._make_request("POST", url, json=data)
    
    async def create_crm_note(
        self,
        module: str,
        record_id: str,
        note_title: str,
        note_content: str
    ) -> Dict[str, Any]:
        """Create a note for CRM record"""
        url = f"{self.crm_base_url}/{module}/{record_id}/Notes"
        
        data = {
            "data": [{
                "Note_Title": note_title,
                "Note_Content": note_content,
                "Parent_Id": record_id
            }]
        }
        
        return await self._make_request("POST", url, json=data)
    
    async def create_crm_task(
        self,
        task_data: Dict[str, Any],
        related_module: Optional[str] = None,
        related_record_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a task in CRM"""
        url = f"{self.crm_base_url}/Tasks"
        
        if related_module and related_record_id:
            task_data["What_Id"] = related_record_id
        
        data = {"data": [task_data]}
        return await self._make_request("POST", url, json=data)
    
    async def transition_blueprint(
        self,
        module: str,
        record_id: str,
        transition_id: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute blueprint transition"""
        url = f"{self.crm_base_url}/{module}/{record_id}/actions/blueprint"
        
        blueprint_data = {
            "blueprint": [{
                "transition_id": transition_id,
                "data": data or {}
            }]
        }
        
        return await self._make_request("PUT", url, json=blueprint_data)
    
    async def attach_file(
        self,
        module: str,
        record_id: str,
        file_path: str,
        file_name: str
    ) -> Dict[str, Any]:
        """Attach file to CRM record - COMPLETE IMPLEMENTATION"""
        url = f"{self.crm_base_url}/{module}/{record_id}/Attachments"

        try:
            # Read file content
            async with aiofiles.open(file_path, 'rb') as file:
                file_content = await file.read()

            # Determine content type based on file extension
            import mimetypes
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'

            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field('file',
                          file_content,
                          filename=file_name,
                          content_type=content_type)
            data.add_field('type', 'attachment')

            # Make request with file upload
            headers = {
                'Authorization': f'Zoho-oauthtoken {await self._get_current_token()}'
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status not in [200, 201]:
                        error_text = await response.text()
                        logger.error(f"File upload failed: {response.status} - {error_text}")
                        raise Exception(f"File upload failed: {response.status} - {error_text}")

                    result = await response.json()
                    logger.info(f"File '{file_name}' uploaded successfully to {module}/{record_id}")
                    return result

        except Exception as e:
            logger.error(f"Error uploading file '{file_name}': {str(e)}")
            raise Exception(f"File upload error: {str(e)}")

    async def _get_current_token(self) -> str:
        """Get current access token, refreshing if needed"""
        await self._ensure_valid_token()
        return self.access_token
    
    # Enhanced CRM methods for Impact Realty workflows
    async def get_crm_record(self, module: str, record_id: str, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get specific CRM record by ID"""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        
        query_string = f"?{urlencode(params)}" if params else ""
        url = f"{self.crm_base_url}/{module}/{record_id}{query_string}"
        return await self._make_request("GET", url)
    
    async def get_crm_records(
        self,
        module: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200,
        sort_by: Optional[str] = None,
        sort_order: str = "asc"
    ) -> Dict[str, Any]:
        """Get multiple CRM records with pagination"""
        params = {
            "page": page,
            "per_page": per_page
        }
        if fields:
            params["fields"] = ",".join(fields)
        if sort_by:
            params["sort_by"] = sort_by
            params["sort_order"] = sort_order
        
        url = f"{self.crm_base_url}/{module}?" + urlencode(params)
        return await self._make_request("GET", url)
    
    async def update_crm_record(self, module: str, record_id: str, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing CRM record"""
        url = f"{self.crm_base_url}/{module}/{record_id}"
        data = {"data": [record_data]}
        return await self._make_request("PUT", url, json=data)
    
    async def delete_crm_record(self, module: str, record_id: str) -> Dict[str, Any]:
        """Delete CRM record"""
        url = f"{self.crm_base_url}/{module}/{record_id}"
        return await self._make_request("DELETE", url)
    
    async def convert_lead(self, lead_id: str, convert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert lead to contact/account/deal"""
        url = f"{self.crm_base_url}/Leads/{lead_id}/actions/convert"
        return await self._make_request("POST", url, json=convert_data)
    
    async def get_related_records(
        self,
        module: str,
        record_id: str,
        related_module: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Get related records for a specific record"""
        params = {
            "page": page,
            "per_page": per_page
        }
        if fields:
            params["fields"] = ",".join(fields)
        
        url = f"{self.crm_base_url}/{module}/{record_id}/{related_module}?" + urlencode(params)
        return await self._make_request("GET", url)
    
    async def create_activity(
        self,
        activity_type: str,  # "Calls", "Events", "Tasks"
        activity_data: Dict[str, Any],
        related_module: Optional[str] = None,
        related_record_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create activity (call, event, task) in CRM"""
        url = f"{self.crm_base_url}/{activity_type}"
        
        if related_module and related_record_id:
            # Link activity to related record
            if activity_type == "Calls":
                activity_data["Who_Id"] = related_record_id
            elif activity_type == "Events":
                activity_data["Who_Id"] = related_record_id
            elif activity_type == "Tasks":
                activity_data["What_Id"] = related_record_id
        
        data = {"data": [activity_data]}
        return await self._make_request("POST", url, json=data)
    
    async def bulk_read(self, module: str, record_ids: List[str], fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """Bulk read multiple records by IDs"""
        url = f"{self.crm_base_url}/{module}/actions/bulk_read"
        
        bulk_data = {
            "data": [{"id": record_id} for record_id in record_ids]
        }
        if fields:
            bulk_data["fields"] = fields
        
        return await self._make_request("POST", url, json=bulk_data)
    
    async def get_field_metadata(self, module: str) -> Dict[str, Any]:
        """Get field metadata for a module"""
        url = f"{self.crm_base_url}/settings/fields?module={module}"
        return await self._make_request("GET", url)
    
    async def get_module_metadata(self, module: str) -> Dict[str, Any]:
        """Get metadata for a specific module"""
        url = f"{self.crm_base_url}/settings/modules/{module}"
        return await self._make_request("GET", url)
    
    # Real Estate specific methods for Impact workflows
    async def search_properties(
        self,
        criteria: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Search properties (assuming custom module or Deals)"""
        return await self.search_crm_records("Deals", criteria, fields, page, per_page)
    
    async def search_agents(
        self,
        criteria: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Search real estate agents (Contacts with agent role)"""
        agent_criteria = f"({criteria}) and (Contact_Role:equals:Agent)"
        return await self.search_crm_records("Contacts", agent_criteria, fields, page, per_page)
    
    async def create_commission_record(
        self,
        agent_id: str,
        deal_id: str,
        commission_amount: float,
        commission_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create commission record for agent"""
        commission_record = {
            "Agent": agent_id,
            "Deal": deal_id,
            "Commission_Amount": commission_amount,
            **commission_data
        }
        
        # Assuming custom Commission module
        return await self.upsert_crm_record("Commissions", commission_record)
    
    # Webhook and notification methods
    async def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook in Zoho CRM"""
        url = f"{self.crm_base_url}/actions/watch"
        return await self._make_request("POST", url, json=webhook_data)
    
    async def send_email(
        self,
        template_id: str,
        recipient_emails: List[str],
        merge_data: Dict[str, Any],
        related_record_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send email using Zoho CRM email templates"""
        email_data = {
            "template_id": template_id,
            "to": recipient_emails,
            "merge_data": merge_data
        }
        
        if related_record_id:
            email_data["related_record"] = related_record_id
        
        url = f"{self.crm_base_url}/actions/send_mail"
        return await self._make_request("POST", url, json=email_data)