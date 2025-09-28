# MCP Files Snapshot - 2025-09-27_13-47-20

## Overview
This snapshot contains a complete backup of all MCP (Model Context Protocol) related files from the ImpactLangFlow project. The snapshot was created on **2025-09-27 at 13:47:20** from git commit `6a2f25fdab48c8fda8d16656ca0c3b65d6a39ae4` on branch `local-dev`.

## Snapshot Statistics
- **Total Files**: 46
- **Total Size**: 1.2MB
- **Source Directory**: `C:\AI_src\ImpactLangFlow`
- **Git Commit**: `6a2f25fdab48c8fda8d16656ca0c3b65d6a39ae4`
- **Git Branch**: `local-dev`

## Directory Structure
```
├── backend/                 # Backend MCP implementation (4 files)
├── config/                  # Environment and Docker configs (5 files)
├── documentation/           # MCP documentation and audits (3 files)
├── flows/                   # LangFlow configurations (6 files)
├── MCPServers/             # MCP server implementations (19 files)
├── scripts/                # Utility and test scripts (4 files)
├── MANIFEST.txt            # Complete file inventory
├── README.md               # This file
└── version_info.txt        # Version metadata
```

## Key Components Included

### 1. Flow Configurations
- **Primary MCP Flow**: `Recruiting Agent 1.5.1 - with MCP Server.json`
- **Supporting Flows**: recruiting.json, admin_compliance.json, office_ops.json, sob_supervisor.json

### 2. Backend Implementation
- **API Routes**: mcp.py (FastAPI endpoints)
- **Data Models**: mcp_schemas.py (Pydantic schemas)
- **Business Logic**: mcp_service.py (Core MCP operations)

### 3. MCP Servers
- **Current Implementation**: zoho-crm-mcp-server/
- **Legacy Implementation**: legacy_zoho_mcp/
- **Consolidated Server**: consolidated_zoho_mcp_server.py

### 4. Configuration
- **Environment Variables**: .env, .env.example, .env.development
- **Container Configuration**: docker-compose.dev.yml
- **MCP-specific configs**: Various .env.local files

### 5. Utilities and Testing
- **Test Scripts**: test_mcp_load.py, validate_flows.py
- **Infrastructure Check**: infrastructure_check.py

## Quick Start for Restoration

1. **Copy files back to source locations** (see MANIFEST.txt for exact paths)
2. **Install dependencies**:
   ```bash
   cd MCPServers/zoho-crm-mcp-server
   pip install -e .
   ```
3. **Configure environment variables** from config/.env.example
4. **Start MCP servers**:
   ```bash
   # Legacy server
   python MCPServers/legacy_zoho_mcp/zoho_mcp_server.py

   # Current server
   cd MCPServers/zoho-crm-mcp-server
   python -m zoho_crm_mcp.server
   ```
5. **Verify with test scripts**:
   ```bash
   python scripts/test_mcp_load.py
   python scripts/validate_flows.py
   ```

## Important Notes

- **Security**: Environment files contain sensitive configurations - handle appropriately
- **Dependencies**: Requires Azure KeyVault access for token management
- **Zoho Integration**: Needs valid Zoho CRM API credentials
- **LangFlow**: Requires LangFlow runtime environment for flow execution

## File Versioning
Each directory contains a `_VERSION_STAMPS.txt` file with detailed version information and source metadata. The complete file inventory is available in `MANIFEST.txt`.

## Created By
Claude Code automated snapshot system on 2025-09-27 13:47:20
Git commit: 6a2f25fdab48c8fda8d16656ca0c3b65d6a39ae4