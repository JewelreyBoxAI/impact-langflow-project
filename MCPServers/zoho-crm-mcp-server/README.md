# Zoho CRM MCP Server Directory - IMPACT REALTY

## 🚀 ACTIVE CONFIGURATION

**Currently Running Server:** `C:\AI_src\ImpactLangFlow\MCPServers\simple_zoho_mcp_server.py`
**Port:** 8001
**Status:** ✅ Production Ready

### Active Files:
- `zoho_langflow_config.json` - **SINGLE ACTIVE ZOHO CONFIGURATION** - Use this for all Langflow operations
- `.env.local` - Working credentials and environment variables
- `src/zoho_crm_mcp/server.py` - Alternative MCP implementation (not currently active)

## 📁 INACTIVE DIRECTORY

Files moved to `inactive/` folder:
- `.tokens.json` - Outdated token storage format
- `langflow_production_nodes.json` - Over-engineered Langflow node configurations
- `langflow_mcp_config_comprehensive.json` - Comprehensive but unused tool definitions

## 🎯 USAGE

For **Langflow integration**, use the single configuration:
```json
// Reference: zoho_langflow_config.json
{
  "server_url": "http://localhost:8001",
  "active_endpoints": {
    "health": "/health",
    "tools": "/mcp/tools",
    "zoho_users": "/zoho/users",
    "zoho_leads": "/zoho/leads"
  }
}
```

## 🔐 CREDENTIALS

All credentials sourced from `.env.local`:
- ZOHO_CLIENT_ID
- ZOHO_CLIENT_SECRET
- ZOHO_REFRESH_TOKEN
- ZOHO_ACCESS_TOKEN
- SALESMSG_API_TOKEN
- OPENAI_API_KEY

## ⚠️ IMPORTANT

- **DO NOT** modify `.env.local` without permission
- **USE** `langflow_active_config.json` for current operations
- **REFERENCE** `langflow_mcp_config.json` for comprehensive tool documentation
- **IGNORE** files in `inactive/` directory
