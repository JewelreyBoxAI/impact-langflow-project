"""
LangFlow Integration Client
HTTP client for LangFlow API communication
"""

import httpx
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class LangFlowClient:
    """Client for LangFlow API integration"""

    def __init__(self):
        # This import is moved from the global scope to inside the function
        # to avoid circular dependency issues on startup.
        
        # FIX 1: Changed from a broken relative import to a robust absolute import.
        from app.config import get_settings
        
        settings = get_settings()
        self.base_url = settings.langflow_base_url
        self.api_key = settings.langflow_api_key

    async def _make_request(self, method: str, endpoint: str, **kwargs):
        """
        Make an authenticated API request to LangFlow using httpx.
        This method correctly handles the async client session.
        """
        url = f"{self.base_url.strip('/')}{endpoint}"
        # The 'async with' block ensures the client session is properly managed.
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                return response.json() if response.content else {}
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error for {url}: {e.response.status_code} - {e.response.text}")
                raise Exception(f"API call to Langflow failed with status {e.response.status_code}") from e
            except Exception as e:
                logger.error(f"An unexpected error occurred calling Langflow at {url}: {str(e)}")
                raise

    async def run_flow(
        self,
        flow_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a LangFlow with given parameters"""
        # The Langflow API endpoint for running flows is different from the UI.
        # It's usually /api/v1/run/{flow_id}
        url = f"/api/v1/run/{flow_id}"

        # The payload for the API is also different.
        # It expects an 'input_value' and other optional parameters.
        payload = {
            "input_value": parameters.get("input_value", ""),
            # You can add other parameters like session_id here if needed
            "session_id": parameters.get("session_id")
        }

        headers = {}
        if self.api_key:
            # FIX 2: Standardized to use the correct 'x-api-key' header.
            headers["x-api-key"] = self.api_key

        try:
            # Note: We are now passing the endpoint, not the full URL.
            response = await self._make_request("POST", url, json=payload, headers=headers, timeout=300)
            return response
        except Exception as e:
            logger.error(f"Error running LangFlow {flow_id}: {str(e)}")
            raise

    async def get_flow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a running LangFlow execution"""
        url = f"/api/v1/executions/{execution_id}/status"

        headers = {}
        if self.api_key:
            # FIX 2: Standardized to use the correct 'x-api-key' header.
            headers["x-api-key"] = self.api_key

        try:
            response = await self._make_request("GET", url, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Error getting flow status {execution_id}: {str(e)}")
            raise

    async def get_available_flows(self) -> Dict[str, Any]:
        """Get list of available flows"""
        url = "/api/v1/flows/"

        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key # This was already correct.

        try:
            response = await self._make_request("GET", url, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Error getting available flows: {str(e)}")
            raise

    async def validate_flow(self, flow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate flow configuration before execution"""
        url = "/api/v1/validate" # This endpoint might be different in your version

        headers = {}
        if self.api_key:
            # FIX 2: Standardized to use the correct 'x-api-key' header.
            headers["x-api-key"] = self.api_key

        try:
            response = await self._make_request("POST", url, json=flow_config, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Error validating flow: {str(e)}")
            raise

