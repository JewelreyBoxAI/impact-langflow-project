"""
LangFlow Integration Client
HTTP client for LangFlow API communication
"""

import httpx
from typing import Dict, Any
import logging
from ..base_client import BaseClient

logger = logging.getLogger(__name__)


class LangFlowClient(BaseClient):
    """Client for LangFlow API integration"""

    def __init__(self):
        from ...app.config import get_settings
        settings = get_settings()
        super().__init__(settings.langflow_base_url)
        self.api_key = settings.langflow_api_key

    async def run_flow(
        self,
        flow_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a LangFlow with given parameters"""
        url = f"/api/v1/flows/{flow_id}/run"

        payload = {
            "input_value": parameters,
            "flow_id": flow_id
        }

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self._make_request("POST", url, json=payload, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Error running LangFlow {flow_id}: {str(e)}")
            raise

    async def get_flow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a running LangFlow execution"""
        url = f"/api/v1/executions/{execution_id}/status"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self._make_request("GET", url, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Error getting flow status {execution_id}: {str(e)}")
            raise

    async def get_available_flows(self) -> Dict[str, Any]:
        """Get list of available flows"""
        url = "/api/v1/flows"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self._make_request("GET", url, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Error getting available flows: {str(e)}")
            raise

    async def validate_flow(self, flow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate flow configuration before execution"""
        url = "/api/v1/flows/validate"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = await self._make_request("POST", url, json=flow_config, headers=headers)
            return response
        except Exception as e:
            logger.error(f"Error validating flow: {str(e)}")
            raise