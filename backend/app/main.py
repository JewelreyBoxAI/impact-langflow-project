"""
FastAPI Application Entry Point for Impact Realty AI Platform
Production-ready FastAPI app with proper structure
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from datetime import datetime

from backend.api.routes import health, crm, flows, realty, webhooks, recruiting, mcp
from backend.app.middleware import audit_middleware
from backend.app.config import get_settings

settings = get_settings()

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title="Impact Realty AI Platform",
        description="Production FastAPI backend for recruiting agent platform with Zoho CRM integration",
        version="1.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add audit middleware
    app.middleware("http")(audit_middleware)

    # Include API routers
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(crm.router, prefix="/api/crm", tags=["CRM"])
    app.include_router(flows.router, prefix="/api/flows", tags=["Flows"])
    app.include_router(realty.router, prefix="/api/realty", tags=["Real Estate"])
    app.include_router(webhooks.router, prefix="/api/webhooks", tags=["Webhooks"])
    app.include_router(recruiting.router, prefix="/api/recruiting", tags=["Recruiting"])
    app.include_router(mcp.router, prefix="/api/mcp", tags=["MCP"])

    @app.on_event("startup")
    async def startup_event():
        """Application startup tasks"""
        logging.basicConfig(
            level=logging.INFO if settings.environment != "production" else logging.WARNING
        )
        logger = logging.getLogger(__name__)
        logger.info(f"Starting Impact Realty AI Platform - Environment: {settings.environment}")

    return app

app = create_app()