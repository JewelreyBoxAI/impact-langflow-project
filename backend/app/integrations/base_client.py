"""
Base asynchronous HTTP client for making API requests.

This class provides a reusable foundation for specific API clients (e.g., Zoho, Langflow)
to handle sessions, requests, and error handling in a consistent way.
"""
import aiohttp
import asyncio
import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class BaseClient:
    """A base class for asynchronous API clients."""

    def __init__(self, base_url: str, headers: Optional[Dict[str, str]] = None):
        """
        Initializes the BaseClient.

        Args:
            base_url: The base URL for the API.
            headers: A dictionary of headers to include in all requests.
        """
        self.base_url = base_url
        self._headers = headers or {}
        self._session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """Asynchronous context manager entry."""
        self._session = aiohttp.ClientSession(headers=self._headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Asynchronous context manager exit."""
        if self._session:
            await self._session.close()

    async def _make_request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Makes an asynchronous HTTP request.

        Args:
            method: The HTTP method (GET, POST, PUT, DELETE).
            endpoint: The API endpoint to call.
            **kwargs: Additional arguments to pass to the request (e.g., json, data, params).

        Returns:
            The JSON response as a dictionary.

        Raises:
            Exception: If the API returns a non-2xx status code.
        """
        if not self._session:
            raise RuntimeError("Client session not started. Use 'async with' syntax.")

        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making {method} request to {url}")

        try:
            async with self._session.request(method, url, **kwargs) as response:
                response_text = await response.text()
                if response.status >= 400:
                    logger.error(
                        f"API Error: {response.status} {response.reason} for URL {url}"
                    )
                    logger.error(f"Response body: {response_text}")
                    response.raise_for_status()

                try:
                    return await response.json()
                except aiohttp.ContentTypeError:
                    logger.debug("Response was not JSON, returning raw text.")
                    return {"raw_response": response_text}
        except aiohttp.ClientError as e:
            logger.error(f"Request failed: {e}")
            raise

    async def get(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Performs a GET request."""
        return await self._make_request("GET", endpoint, **kwargs)

    async def post(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Performs a POST request."""
        return await self._make_request("POST", endpoint, **kwargs)

    async def put(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Performs a PUT request."""
        return await self._make_request("PUT", endpoint, **kwargs)

    async def delete(self, endpoint: str, **kwargs: Any) -> Dict[str, Any]:
        """Performs a DELETE request."""
        return await self._make_request("DELETE", endpoint, **kwargs)
