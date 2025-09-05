"""
LangFlow client for communicating with LangFlow server
"""

import aiohttp
import asyncio
import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class LangFlowClient:
    """Async client for LangFlow API communication"""
    
    def __init__(self):
        self.base_url = os.getenv("LANGFLOW_URL", "http://localhost:7860")
        self.api_key = os.getenv("LANGFLOW_API_KEY", "")
        self.timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
        
    async def run_flow(
        self,
        flow_id: str,
        input_data: Dict[str, Any],
        session_id: Optional[str] = None,
        tweaks: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Run a LangFlow flow with given inputs
        
        Args:
            flow_id: The LangFlow flow ID to execute
            input_data: Input data for the flow
            session_id: Optional session ID for conversation continuity
            tweaks: Optional parameter tweaks for the flow
            
        Returns:
            Flow execution response with outputs and metadata
        """
        url = f"{self.base_url}/api/v1/run/{flow_id}"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        payload = {
            "input_value": input_data.get("input", ""),
            "output_type": "chat",
            "input_type": "chat"
        }
        
        if session_id:
            payload["session_id"] = session_id
            
        if tweaks:
            payload["tweaks"] = tweaks
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                logger.info(f"Running flow {flow_id} with payload: {json.dumps(payload, indent=2)}")
                
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"Flow {flow_id} completed successfully")
                        
                        # Extract the response from LangFlow's structure
                        outputs = result.get("outputs", [])
                        if outputs and len(outputs) > 0:
                            # Get the first output (typically the chat response)
                            output = outputs[0]
                            
                            # Extract message content
                            results = output.get("results", {})
                            message_data = results.get("message", {})
                            
                            if isinstance(message_data, dict):
                                message_content = message_data.get("text", message_data.get("content", "No response"))
                            else:
                                message_content = str(message_data)
                            
                            # Extract metadata
                            metadata = {
                                "session_id": result.get("session_id"),
                                "flow_id": flow_id,
                                "execution_time": datetime.utcnow().isoformat(),
                                "record_ids": self._extract_record_ids(result),
                                "links": self._extract_links(result)
                            }
                            
                            return {
                                "success": True,
                                "outputs": {
                                    "message": message_content
                                },
                                "metadata": metadata,
                                "raw_response": result
                            }
                        else:
                            logger.warning(f"No outputs received from flow {flow_id}")
                            return {
                                "success": False,
                                "outputs": {
                                    "message": "No response received from the flow"
                                },
                                "metadata": {},
                                "raw_response": result
                            }
                    else:
                        error_text = await response.text()
                        logger.error(f"Flow execution failed: {response.status} - {error_text}")
                        raise Exception(f"Flow execution failed: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout executing flow {flow_id}")
            raise Exception("Flow execution timed out")
        except Exception as e:
            logger.error(f"Error executing flow {flow_id}: {str(e)}")
            raise Exception(f"Flow execution error: {str(e)}")
    
    def _extract_record_ids(self, response: Dict[str, Any]) -> list:
        """Extract record IDs from flow response"""
        record_ids = []
        
        # Look for common patterns in the response
        response_str = json.dumps(response)
        
        # Common Zoho CRM ID patterns
        import re
        zoho_id_pattern = r'\b\d{19}\b'  # Zoho IDs are typically 19 digits
        matches = re.findall(zoho_id_pattern, response_str)
        record_ids.extend(matches)
        
        return list(set(record_ids))  # Remove duplicates
    
    def _extract_links(self, response: Dict[str, Any]) -> list:
        """Extract URLs/links from flow response"""
        links = []
        
        # Look for URLs in the response
        response_str = json.dumps(response)
        
        import re
        url_pattern = r'https?://[^\s<>"{}|\\^`[\]]+[^\s<>"{}|\\^`[\].,;:]'
        matches = re.findall(url_pattern, response_str)
        links.extend(matches)
        
        return list(set(links))  # Remove duplicates
    
    async def get_flow_status(self, flow_id: str) -> Dict[str, Any]:
        """Get status/info about a specific flow"""
        url = f"{self.base_url}/api/v1/flows/{flow_id}"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to get flow status: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error getting flow status for {flow_id}: {str(e)}")
            raise
    
    async def list_flows(self) -> Dict[str, Any]:
        """List all available flows"""
        url = f"{self.base_url}/api/v1/flows"
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        raise Exception(f"Failed to list flows: {response.status} - {error_text}")
        except Exception as e:
            logger.error(f"Error listing flows: {str(e)}")
            raise