# Enhanced Impact Realty MCP Server

## 🚀 Overview

Your existing Zoho MCP Server has been significantly enhanced and adapted for the Impact Realty AI Platform. The server now provides comprehensive Zoho CRM integration with advanced features, secure credential management, and real estate-specific functionality.

## ✨ New Features Added

### 🔐 **Azure Key Vault Integration**
- Secure credential storage and retrieval
- Automatic fallback to environment variables
- Credential caching for performance
- Health monitoring for Key Vault connectivity

### 📊 **Enhanced CRM Operations**
- **CRUD Operations**: Get, List, Update, Delete records
- **Lead Management**: Convert leads with workflow automation
- **Related Records**: Fetch associated records across modules
- **Activity Management**: Create calls, events, tasks
- **Bulk Operations**: Bulk read multiple records
- **Metadata Access**: Field and module metadata retrieval

### 🏠 **Real Estate Specific Features**
- **Property Search**: Specialized property queries
- **Agent Management**: Real estate agent search and management
- **Commission Tracking**: Automated commission record creation
- **Custom Field Mapping**: Real estate industry field mappings

### 📧 **Communication & Automation**
- **Email Templates**: Send emails via Zoho CRM templates
- **Webhook Management**: Create and manage webhooks
- **Blueprint Automation**: Execute CRM blueprint transitions
- **File Attachments**: Attach files to CRM records

### 🔧 **Operational Improvements**
- **Comprehensive Health Checks**: Multi-service health monitoring
- **Advanced Logging**: Structured logging with multiple levels
- **Rate Limiting**: Intelligent API rate limit management
- **Retry Logic**: Exponential backoff for failed requests
- **OAuth Management**: Automatic token refresh and caching

## 🏗️ Architecture

```
Impact LangFlow Platform
├── LangFlow Orchestrator (Frontend)
├── MCP Server (This Component)
│   ├── FastAPI REST API
│   ├── Zoho CRM Client
│   ├── Azure Key Vault Client
│   └── Pydantic Schemas
├── Streamlit UI
└── Azure Infrastructure
    ├── PostgreSQL Database
    ├── Redis Cache
    └── Key Vault (Credentials)
```

## 🛠️ API Endpoints

### **Core CRM Endpoints**
```http
GET    /health                           # Comprehensive health check
GET    /zoho/crm/{module}               # List records with pagination
GET    /zoho/crm/{module}/{record_id}   # Get specific record
PUT    /zoho/crm/{module}/{record_id}   # Update record
DELETE /zoho/crm/{module}/{record_id}   # Delete record
POST   /zoho/crm/search                 # Search records
POST   /zoho/crm/upsert                 # Create/update records
```

### **Advanced CRM Endpoints**
```http
POST   /zoho/leads/{lead_id}/convert           # Convert lead
GET    /zoho/crm/{module}/{id}/{related}      # Get related records
POST   /zoho/crm/activities/create            # Create activities
POST   /zoho/crm/{module}/bulk_read           # Bulk read records
GET    /zoho/metadata/fields/{module}         # Field metadata
GET    /zoho/metadata/modules/{module}        # Module metadata
```

### **Real Estate Endpoints**
```http
POST   /zoho/realty/properties/search    # Search properties
POST   /zoho/realty/agents/search        # Search agents
POST   /zoho/realty/commissions/create   # Create commission records
```

### **Communication Endpoints**
```http
POST   /zoho/webhooks/create    # Create webhooks
POST   /zoho/email/send         # Send template emails
```

### **Legacy Endpoints (Maintained)**
```http
POST   /zoho/flow/run                    # Execute Zoho Flow
GET    /zoho/flow/status/{execution_id}  # Flow status
POST   /zoho/crm/notes/create           # Create notes
POST   /zoho/crm/tasks/create           # Create tasks
POST   /zoho/blueprint/transition       # Blueprint transitions
POST   /zoho/files/attach               # Attach files
```

## 🔧 Configuration

### **Environment Variables**
```bash
# Azure Key Vault
AZURE_KEY_VAULT_NAME=kv-impact-platform-v2

# Server Configuration
MCP_SERVER_HOST=0.0.0.0
MCP_SERVER_PORT=8000
ENVIRONMENT=production
LOG_LEVEL=INFO

# Fallback Credentials (if Key Vault unavailable)
ZOHO_CLIENT_ID=your-client-id
ZOHO_CLIENT_SECRET=your-client-secret
ZOHO_REFRESH_TOKEN=your-refresh-token
```

### **Azure Key Vault Secrets**
The server expects these secrets in Azure Key Vault:
```
zoho-client-id          # Zoho OAuth Client ID
zoho-client-secret      # Zoho OAuth Client Secret
zoho-refresh-token      # Zoho OAuth Refresh Token
zoho-access-token       # Cached access token (optional)
openai-api-key         # OpenAI API key
anthropic-api-key      # Anthropic API key
langflow-api-key       # LangFlow API key
```

## 🚀 Getting Started

### **1. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **2. Configure Azure Authentication**
```bash
# Login to Azure (if not already authenticated)
az login --tenant anthonyyummyimagemedia.onmicrosoft.com

# Verify Key Vault access
az keyvault secret list --vault-name kv-impact-platform-v2
```

### **3. Start the Server**
```bash
# Using the startup script (recommended)
python mcp_server/startup.py

# Or using uvicorn directly
uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000 --reload
```

### **4. Verify Installation**
```bash
# Health check
curl http://localhost:8000/health

# API documentation
open http://localhost:8000/docs
```

## 🔍 Health Monitoring

The enhanced health endpoint provides comprehensive status:

```json
{
  "status": "healthy",
  "timestamp": "2024-09-04T18:30:00Z",
  "services": {
    "key_vault": {
      "status": "healthy",
      "vault_name": "kv-impact-platform-v2"
    },
    "zoho_credentials": {
      "client_id": true,
      "client_secret": true, 
      "refresh_token": true
    }
  },
  "version": "1.0.0",
  "server": "Impact Realty MCP Server"
}
```

## 🏠 LangFlow Integration

The MCP server is designed to be called from LangFlow agents:

### **Example LangFlow Node Configuration**
```json
{
  "component_name": "HTTPRequestTool",
  "url": "http://localhost:8000/zoho/crm/search",
  "method": "POST",
  "headers": {"Content-Type": "application/json"},
  "body": {
    "module": "Leads",
    "criteria": "Email:equals:{user_email}",
    "fields": ["First_Name", "Last_Name", "Email", "Phone"]
  }
}
```

## 🛡️ Security Features

- **Azure Key Vault**: Secure credential storage
- **OAuth Token Management**: Automatic refresh and caching
- **Rate Limiting**: API request throttling
- **Request Validation**: Pydantic schema validation
- **Audit Logging**: Comprehensive request/response logging
- **CORS Configuration**: Controlled cross-origin access

## 📊 Real Estate Workflows

### **Lead Processing**
1. Search existing leads in CRM
2. Create new lead if not found
3. Associate with agent and property
4. Create follow-up tasks
5. Send email notifications

### **Commission Processing**
1. Search for deal closure
2. Calculate commission amounts
3. Create commission records
4. Link to agent profiles
5. Generate commission reports

### **Agent Management**
1. Search active agents
2. Update agent profiles
3. Track performance metrics
4. Assign leads and properties
5. Generate agent reports

## 🔧 Troubleshooting

### **Common Issues**

**Key Vault Access Denied**
```bash
# Check Azure login status
az account show

# Verify Key Vault permissions
az keyvault secret list --vault-name kv-impact-platform-v2
```

**Zoho Authentication Errors**
```bash
# Check credential availability
curl http://localhost:8000/health | jq .services.zoho_credentials
```

**Server Won't Start**
```bash
# Check port availability
netstat -an | grep 8000

# Check dependencies
pip check
```

## 📈 Performance

- **Credential Caching**: LRU cache for Key Vault secrets
- **Connection Pooling**: Async HTTP client connection reuse
- **Rate Limiting**: Intelligent request throttling
- **Bulk Operations**: Efficient multi-record processing
- **Lazy Loading**: On-demand credential retrieval

## 🔄 Migration from Basic MCP Server

Your existing Zoho MCP server functionality is **fully preserved**. All previous endpoints work unchanged, with these enhancements:

✅ **Backward Compatible**: Existing integrations continue to work  
✅ **Enhanced Security**: Credentials now secured in Key Vault  
✅ **Better Error Handling**: Comprehensive retry logic  
✅ **Health Monitoring**: Detailed service status checks  
✅ **Advanced Features**: 15+ new endpoints for expanded functionality  

## 🎯 Impact Realty Specific Benefits

- **Agent Onboarding**: Automated agent profile creation and management
- **Lead Distribution**: Intelligent lead assignment to agents
- **Commission Tracking**: Automated commission calculations and reporting
- **Property Management**: Enhanced property search and categorization
- **Client Communication**: Template-based email automation
- **Performance Analytics**: Agent and property performance metrics
- **Compliance Tracking**: Automated compliance and documentation

This enhanced MCP server provides a robust foundation for the Impact Realty AI Platform's multi-agent architecture while maintaining full compatibility with your existing workflows.