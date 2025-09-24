"""
LangFlow Service
Business logic for LangFlow operations
"""

from typing import Dict, Any
import logging

from ..integrations.langflow.client import LangFlowClient

logger = logging.getLogger(__name__)


class LangFlowService:
    """Service class for LangFlow business operations"""

    def __init__(self):
        self.client = LangFlowClient()

    async def run_flow(
        self,
        flow_id: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a LangFlow with given parameters"""
        # Add execution context for Impact Realty
        execution_context = {
            'platform': 'Impact Realty AI',
            'execution_time': parameters.get('timestamp'),
            'user_context': parameters.get('user_id', 'system')
        }

        # Merge execution context with parameters
        enhanced_parameters = {**parameters, 'context': execution_context}

        return await self.client.run_flow(flow_id, enhanced_parameters)

    async def get_flow_status(self, execution_id: str) -> Dict[str, Any]:
        """Get status of a running LangFlow execution"""
        return await self.client.get_flow_status(execution_id)

    async def get_available_flows(self) -> Dict[str, Any]:
        """Get list of available flows"""
        return await self.client.get_available_flows()

    async def validate_flow(self, flow_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate flow configuration before execution"""
        return await self.client.validate_flow(flow_config)