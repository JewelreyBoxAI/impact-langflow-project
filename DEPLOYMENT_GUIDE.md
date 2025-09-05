# Impact Realty AI Platform - Deployment Guide

## 🚀 Azure Infrastructure Status

**✅ Completed Resources (Impact Tenant: `rg-Impact-AgenticSystems`):**
- **PostgreSQL Server**: `impact-ai-postgres-v2.postgres.database.azure.com`
- **Redis Cache**: `impact-ai-redis.redis.cache.windows.net` 
- **Key Vault**: `kv-impact-platform-v2` ✅ **ALL CREDENTIALS STORED**

## 🔑 ✅ Key Vault Ready - All Credentials Stored!

**The Key Vault `kv-impact-platform-v2` is fully configured with all credentials:**

✅ **PostgreSQL credentials** (connection string, host, user, password)  
✅ **Redis credentials** (connection string, host, password)  
✅ **Zoho integration** (client ID, secret, redirect URI, base URL)  
✅ **Communications** (Salesmsg token, ManyChat token, default inbox)  
✅ **Application settings** (LangFlow URL, MCP server URL, timezone, environment)

**No additional Key Vault setup needed** - proceed directly to Step 3!

**Key Vault Contents:**
```bash
# View all stored secrets
az keyvault secret list --vault-name kv-impact-platform-v2 --output table

# Test access to a secret
az keyvault secret show --vault-name kv-impact-platform-v2 --name "POSTGRES-CONNECTION-STRING" --query value -o tsv
```

## 📋 Step 3: Environment Configuration

Copy the production environment file:
```bash
cp .env.impact .env
```

The `.env.impact` file contains:
- ✅ **Azure credentials** (PostgreSQL, Redis, Key Vault)
- ✅ **Zoho integration** (from your dev environment)
- ✅ **Communications** (Salesmsg, ManyChat)
- ⏳ **Pending integrations** (Google, MLS, OpenAI, etc.)

## 🔧 Step 4: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "import langflow, streamlit, fastapi; print('All dependencies installed successfully')"
```

## 🏃‍♂️ Step 5: Start the Platform

### Terminal 1: MCP Server (Zoho Integration)
```bash
cd mcp_server
python main.py
# Server starts on http://localhost:8000
```

### Terminal 2: LangFlow Server
```bash
langflow run --host 0.0.0.0 --port 7860
# LangFlow UI: http://localhost:7860
```

### Terminal 3: Import LangFlow Flows
1. Open http://localhost:7860
2. Import each JSON file from `flows/` directory:
   - `sob_supervisor.json` (Kevin's S1-S8 agents)
   - `office_ops.json` (Eileen's A1-A12 agents)
   - `recruiting.json` (Katelyn's K0-K3 agents)
   - `admin_compliance.json` (Karen's executive assistant)

### Terminal 4: Streamlit Chat UI
```bash
cd streamlit_app
streamlit run app.py
# Chat UI: http://localhost:8501
```

## 🎯 Step 6: Phase 1 Testing

Start with the **Admin & Compliance (Karen)** and **Recruiting (Katelyn)** modules:

### Test Karen's Executive Assistant:
1. Go to Streamlit UI: http://localhost:8501
2. Select "Karen's Executive Assistant" 
3. Test queries like:
   - "Show me recent leads in Zoho CRM"
   - "Create a follow-up task for lead John Doe"
   - "Search for agents with expired licenses"

### Test Katelyn's Recruiting:
1. Select "Katelyn's Recruiting"
2. Test scenarios:
   - "Process new agent lead: Jane Smith, licensed, 3 years experience"
   - "Send outreach message to experienced agent prospects"
   - "Schedule interview for qualified candidate"

## 📊 Step 7: Monitor & Verify

### Check Azure Resources:
```bash
# PostgreSQL connectivity
az postgres flexible-server connect -n impact-ai-postgres-v2 -u impactadmin -d postgres

# Redis status
az redis show -n impact-ai-redis -g rg-Impact-AgenticSystems --query provisioningState

# Key Vault access
az keyvault secret list --vault-name kv-impact-credentials
```

### Check Application Logs:
- **MCP Server**: Console output in Terminal 1
- **LangFlow**: Execution logs in LangFlow UI
- **Streamlit**: Browser console and Terminal 4

## 🔄 Step 8: Next Phase Deployment

### Phase 2: Office Operations (Eileen)
- Deploy A1-A12 agents for back-office automation
- Connect bank APIs for commission processing
- Set up DBPR license monitoring

### Phase 3: SOB Supervisor (Kevin)
- Deploy S1-S8 supervisor agents
- Set up executive reporting and KPIs
- Configure MLS portfolio management

## 🚨 Troubleshooting

### Common Issues:

**Key Vault Access Denied:**
- Verify RBAC role assignment completed
- Wait 5-10 minutes for permission propagation
- Try `az login --tenant 4ceaeb6a-c5a7-40cd-98ef-a578bc94192f`

**PostgreSQL Connection:**
- Ensure firewall allows Azure services
- Verify connection string format
- Test: `az postgres flexible-server connect`

**Redis Connection:**
- Check if Redis is fully provisioned
- Verify SSL connection (port 6380)
- Test connection string format

**LangFlow Import Issues:**
- Check JSON validity: `python -m json.tool flows/recruiting.json`
- Ensure all environment variables are set
- Verify MCP server is running on port 8000

### Support Resources:
- Azure Monitor for infrastructure logs
- LangFlow execution history for flow debugging
- MCP server logs for integration issues

## 🎉 Success Criteria

**Phase 1 Complete When:**
- ✅ All 4 LangFlow flows import successfully
- ✅ MCP server responds to Zoho API calls
- ✅ Karen's assistant can query CRM data
- ✅ Katelyn's recruiting processes new leads
- ✅ Chat UI shows conversation history
- ✅ Azure Key Vault stores all credentials securely

---

**Impact Realty AI Platform** - Ready for intelligent automation! 🏠🤖