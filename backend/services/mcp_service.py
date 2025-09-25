"""
MCP (Model Context Protocol) Service
Business logic for MCP server operations
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
import httpx

from ..schemas.mcp_schemas import MCPServerStatus, MCPServerConfig
from ..integrations.MCPClients.zoho_mcp_client import ZohoMCPClient

logger = logging.getLogger(__name__)

class MCPService:
    """Service class for MCP server operations"""

    def __init__(self):
        self.zoho_mcp_client = ZohoMCPClient()
        self.server_configs = self._load_server_configs()
        self.client = httpx.AsyncClient(timeout=30.0)

    def _load_server_configs(self) -> Dict[str, MCPServerConfig]:
        """Load MCP server configurations"""
        return {
            "zoho": MCPServerConfig(
                server_name="zoho",
                host="localhost",
                port=3001,
                protocol="http"
            ),
            "gmail": MCPServerConfig(
                server_name="gmail",
                host="localhost",
                port=3002,
                protocol="http"
            ),
            "salesmsg": MCPServerConfig(
                server_name="salesmsg",
                host="localhost",
                port=3003,
                protocol="http"
            )
        }

    async def get_all_servers_status(self) -> List[MCPServerStatus]:
        """Get status of all configured MCP servers"""
        statuses = []

        for server_name, config in self.server_configs.items():
            try:
                start_time = time.time()
                status = await self._ping_server(config)
                response_time = (time.time() - start_time) * 1000

                statuses.append(MCPServerStatus(
                    server_name=server_name,
                    status="online" if status else "offline",
                    response_time=response_time if status else None,
                    last_ping=time.strftime("%Y-%m-%d %H:%M:%S") if status else None
                ))

            except Exception as e:
                logger.error(f"Error checking status of {server_name}: {str(e)}")
                statuses.append(MCPServerStatus(
                    server_name=server_name,
                    status="error",
                    error_message=str(e)
                ))

        return statuses

    async def _ping_server(self, config: MCPServerConfig) -> bool:
        """Ping MCP server to check if it's alive"""
        try:
            url = f"{config.protocol}://{config.host}:{config.port}/health"
            response = await self.client.get(url, timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def restart_server(self, server_name: str) -> Dict[str, Any]:
        """Restart specific MCP server"""
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown server: {server_name}")

        config = self.server_configs[server_name]

        try:
            url = f"{config.protocol}://{config.host}:{config.port}/admin/restart"
            response = await self.client.post(url)

            if response.status_code == 200:
                # Wait for server to come back online
                await asyncio.sleep(3)
                is_online = await self._ping_server(config)

                return {
                    "success": True,
                    "online": is_online,
                    "message": f"Server {server_name} restart initiated"
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to restart server: HTTP {response.status_code}"
                }

        except Exception as e:
            logger.error(f"Error restarting server {server_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def dedupe_zoho_prospects(
        self,
        prospects: List[Dict[str, Any]],
        dedupe_fields: List[str]
    ) -> Dict[str, Any]:
        """Deduplicate prospects against Zoho CRM"""
        try:
            start_time = time.time()

            result = await self.zoho_mcp_client.dedupe_prospects(
                prospects=prospects,
                dedupe_fields=dedupe_fields
            )

            processing_time = time.time() - start_time

            return {
                **result,
                "processing_time": processing_time
            }

        except Exception as e:
            logger.error(f"Error in Zoho deduplication: {str(e)}")
            raise

    async def send_request(
        self,
        server_name: str,
        method: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send generic request to MCP server"""
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown server: {server_name}")

        config = self.server_configs[server_name]

        try:
            start_time = time.time()
            url = f"{config.protocol}://{config.host}:{config.port}/mcp/{method}"

            response = await self.client.post(
                url,
                json=params,
                headers={"Content-Type": "application/json"}
            )

            execution_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                return {
                    "success": True,
                    "result": response.json(),
                    "execution_time": execution_time
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "execution_time": execution_time
                }

        except Exception as e:
            logger.error(f"Error sending MCP request to {server_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def check_server_health(self, server_name: str) -> Dict[str, Any]:
        """Check detailed health of specific MCP server"""
        if server_name not in self.server_configs:
            raise ValueError(f"Unknown server: {server_name}")

        config = self.server_configs[server_name]

        try:
            start_time = time.time()
            url = f"{config.protocol}://{config.host}:{config.port}/health/detailed"

            response = await self.client.get(url)
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                health_data = response.json()
                return {
                    "healthy": True,
                    "response_time": response_time,
                    "details": health_data
                }
            else:
                return {
                    "healthy": False,
                    "response_time": response_time,
                    "error": f"HTTP {response.status_code}"
                }

        except Exception as e:
            logger.error(f"Error checking health of {server_name}: {str(e)}")
            return {
                "healthy": False,
                "error": str(e)
            }

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.client.aclose()