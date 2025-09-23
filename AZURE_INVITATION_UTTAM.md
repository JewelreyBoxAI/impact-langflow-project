# Azure Access Invitation for UTTAM@blackcoffer.com

## 🎯 **Your Azure Access is Ready!**

Hi UTTAM,

Your Azure access has been configured for the Impact Realty AI Platform development. **No manual approval required** - everything is automated once you accept the invitation.

---

## 📧 **Step 1: Accept Azure Invitation**

Check your email (**UTTAM@blackcoffer.com**) for:
- **Subject**: "You've been invited to Impact Realty's Azure tenant"
- **From**: Microsoft Azure / anthonyyummyimagemedia.onmicrosoft.com

**Click "Accept Invitation"** in the email to activate your access.

---

## 🔐 **Step 2: Login to Azure**

```bash
# Login to the Impact tenant
az login --tenant anthonyyummyimagemedia.onmicrosoft.com

# Verify you're in the correct tenant
az account show
```

**Expected Output**:
```json
{
  "tenantId": "4ceaeb6a-c5a7-40cd-98ef-a578bc94192f",
  "name": "Impact Realty Subscription",
  "user": {
    "name": "UTTAM@blackcoffer.com"
  }
}
```

---

## 🗝️ **Your Full Access Permissions**

### **✅ PostgreSQL Database** (Production Ready)
```bash
# Connection Details
Host: impact-ai-postgres-v2.postgres.database.azure.com
Port: 5432
Database: postgres
Username: impactadmin
Password: [Available in Key Vault: "postgres-password"]

# Direct Connection String
postgresql://impactadmin:[password]@impact-ai-postgres-v2.postgres.database.azure.com:5432/postgres?sslmode=require

# Test Connection
psql "postgresql://impactadmin:[get-password-from-keyvault]@impact-ai-postgres-v2.postgres.database.azure.com:5432/postgres?sslmode=require"
```

### **✅ Redis Cache** (Production Ready)
```bash
# Connection Details  
Host: impact-ai-redis.redis.cache.windows.net
Port: 6380 (SSL) / 6379 (non-SSL)
Password: [Available in Key Vault: "redis-password"]

# Direct Connection
redis-cli -h impact-ai-redis.redis.cache.windows.net -p 6380 -a "[get-from-keyvault]" --tls
```

### **✅ Azure Key Vault** (Full Access)
```bash
# List all secrets
az keyvault secret list --vault-name kv-impact-platform-v2 --output table

# Get a specific secret
az keyvault secret show --vault-name kv-impact-platform-v2 --name "postgres-password" --query value -o tsv

# Store new secrets
az keyvault secret set --vault-name kv-impact-platform-v2 --name "your-secret-name" --value "your-secret-value"
```

---

## 🏗️ **Development Resources Available**

### **Resource Group**: `rg-Impact-AgenticSystems`
```bash
# List all resources
az resource list --resource-group rg-Impact-AgenticSystems --output table
```

### **Infrastructure Status**: ✅ **FULLY OPERATIONAL**
| Service | Name | Status | Access |
|---------|------|---------|---------|
| **PostgreSQL** | `impact-ai-postgres-v2` | ✅ Running | Direct connection |
| **Redis Cache** | `impact-ai-redis` | ✅ Running | Direct connection |
| **Key Vault** | `kv-impact-platform-v2` | ✅ Active | Full read/write |

---

## 🚀 **Quick Start Development**

### **1. Clone the Project**
```bash
git clone https://github.com/JewelreyBoxAI/impact-langflow-project.git
cd impact-langflow-project
```

### **2. Setup Environment**
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Get credentials from Key Vault
az keyvault secret show --vault-name kv-impact-platform-v2 --name "postgres-password" --query value -o tsv
az keyvault secret show --vault-name kv-impact-platform-v2 --name "redis-password" --query value -o tsv
```

### **3. Start the Platform**
```bash
# Start MCP Server
cd mcp_server && python startup.py &

# Start LangFlow  
langflow run --host 0.0.0.0 --port 7860 &

# Start Streamlit UI
cd streamlit_app && streamlit run app.py
```

---

## 🔧 **Available Services & APIs**

### **MCP Server** (Enhanced Zoho Integration)
- **URL**: `http://localhost:8000`
- **Health Check**: `curl http://localhost:8000/health`
- **API Docs**: `http://localhost:8000/docs`
- **Features**: 15+ Zoho CRM endpoints, real estate workflows, Key Vault integration

### **LangFlow Orchestrator**
- **URL**: `http://localhost:7860`  
- **Flows Available**: 4 pre-built workflows (SOB, Office Ops, Recruiting, Admin)
- **Integration**: Direct MCP server connectivity

### **Streamlit UI**
- **URL**: `http://localhost:8501`
- **Features**: ChatGPT-style interface with persistent chat history

---

## 📊 **Stored Credentials (Key Vault)**

Your Key Vault contains **19 production credentials**:

### **Core Infrastructure**
- `postgres-password` - Database access
- `redis-password` - Cache access

### **Zoho Integration** 
- `zoho-client-id` - OAuth client ID
- `zoho-client-secret` - OAuth client secret  
- `zoho-refresh-token` - OAuth refresh token

### **Communication Services**
- `salesmsg-api-token` - SMS service
- `manychat-api-token` - Chat automation
- `twilio-account-sid` / `twilio-auth-token` - Backup SMS

### **AI Services**
- `openai-api-key` - GPT models
- `anthropic-api-key` - Claude models
- `langflow-api-key` - LangFlow API

### **Real Estate APIs**
- `mls-api-key` - Property data
- `dbpr-api-key` - License verification
- `brokersumo-api-key` - Commission processing

---

## 🛡️ **Security Features**

### **✅ Zero Manual Approval Required**
- Automatic guest user permissions
- Pre-configured access policies  
- No Anthony/admin intervention needed

### **✅ Network Access**
- PostgreSQL: **Open to all IPs** (development friendly)
- Redis: **Public network enabled**
- Key Vault: **Public access** with access policies

### **✅ Development Ready**
- Full CRUD access to databases
- Complete secrets management
- Direct infrastructure connectivity

---

## 🎯 **What You Can Build**

### **Multi-Agent Workflows**
- **SOB Supervisor (Kevin)**: Executive oversight and KPI monitoring
- **Office Operations (Eileen)**: Commission processing and back-office automation
- **Recruiting (Katelyn)**: Agent onboarding and lead management
- **Admin & Compliance (Karen)**: Administrative task automation

### **Real Estate Features**
- Property search and management
- Agent performance tracking
- Commission calculations and reporting
- Lead distribution and follow-up
- Compliance monitoring and documentation

### **Integration Capabilities**
- Zoho CRM/Flow automation
- MLS property data integration
- SMS/email communication workflows
- Document generation and processing
- Calendar and task management

---

## 📞 **Support & Resources**

### **Documentation**
- **Project README**: Full platform overview
- **MCP Server Docs**: API reference and examples
- **Deployment Guide**: Production deployment instructions

### **Health Monitoring**
```bash
# Check all services
curl http://localhost:8000/health | jq

# Test database connection
az postgres flexible-server connect -n impact-ai-postgres-v2 -g rg-Impact-AgenticSystems -u impactadmin

# Test Redis connection  
redis-cli -h impact-ai-redis.redis.cache.windows.net -p 6380 ping
```

### **Troubleshooting**
- **Azure Login Issues**: Use `az account clear && az login --tenant anthonyyummyimagemedia.onmicrosoft.com`
- **Key Vault Access**: Verify with `az keyvault secret list --vault-name kv-impact-platform-v2`
- **Database Connection**: Check firewall rules and connection strings

---

## 🚀 **Ready to Start!**

1. ✅ **Accept the Azure invitation email**
2. ✅ **Login to Azure CLI with the tenant**
3. ✅ **Clone the GitHub repository** 
4. ✅ **Start building Impact's AI platform!**

**You have complete development access to Impact Realty's AI infrastructure with zero restrictions.**

---

**Happy Coding! 🎉**

*The Impact Realty AI Platform team*