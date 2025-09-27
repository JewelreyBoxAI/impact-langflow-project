"""
FastAPI Middleware
Request/response processing middleware
"""

from fastapi import Request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


async def audit_middleware(request: Request, call_next):
    """Log all API calls for auditing"""
    start_time = datetime.utcnow()

    response = await call_next(request)

    process_time = (datetime.utcnow() - start_time).total_seconds()

    logger.info(f"API Call: {request.method} {request.url.path} - "
               f"Status: {response.status_code} - Duration: {process_time:.3f}s")

    return response