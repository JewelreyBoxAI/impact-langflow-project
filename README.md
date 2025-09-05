# Impact Realty AI Platform

A comprehensive multi-agent AI platform built for Impact Realty using LangFlow orchestration, Azure infrastructure, and Streamlit chat interface. The platform automates operations across four key areas: SOB Supervision (Kevin), Office Operations (Eileen), Recruiting (Katelyn), and Admin & Compliance (Karen).

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Impact Realty AI Platform                    │
├─────────────────────────────────────────────────────────────────┤
│  Frontend: Streamlit Chat UI (ChatGPT-style interface)         │
├─────────────────────────────────────────────────────────────────┤
│  Orchestration: LangFlow (4 separate flow files)               │
│  ├── SOB Supervisor (Kevin) - S1-S8 agents                     │
│  ├── Office Operations (Eileen) - A1-A12 agents               │
│  ├── Recruiting (Katelyn) - K0-K3 agents                      │
│  └── Admin & Compliance (Karen) - Executive orchestrator       │
├─────────────────────────────────────────────────────────────────┤
│  Integration Layer: FastAPI MCP Server                         │
│  └── Zoho CRM, Flow, Google, MLS, Salesmsg, Apify, etc.       │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure: Azure (Impact's tenant)                       │
│  ├── PostgreSQL (chat persistence & audit logs)               │
│  ├── Redis (session memory & caching)                         │
│  ├── Key Vault (secrets management)                           │
│  └── Resource Group: rg-Impact-AgenticSystems                 │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
ImpactLangFlow/
├── flows/                              # LangFlow JSON definitions
│   ├── sob_supervisor.json            # Kevin's S1-S8 supervisor agents
│   ├── office_ops.json               # Eileen's A1-A12 operations agents  
│   ├── recruiting.json               # Katelyn's K0-K3 recruiting agents
│   └── admin_compliance.json         # Karen's executive assistant
├── mcp_server/                        # FastAPI MCP integration server
│   ├── main.py                       # FastAPI app with Zoho endpoints
│   ├── zoho_client.py               # OAuth wrapper & API client
│   ├── schemas.py                   # Pydantic request/response models
│   └── README.md                    # MCP server documentation
├── streamlit_app/                     # ChatGPT-style UI
│   ├── app.py                       # Main Streamlit chat interface
│   ├── lf_client.py                 # LangFlow API client
│   └── db.py                        # PostgreSQL & Redis helpers
├── tests/                            # Test suite
│   └── test_basic.py                # JSON validity & endpoint tests
├── .env.example                      # Environment variable template
├── requirements.txt                  # Pinned Python dependencies
└── README.md                         # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Azure CLI (logged into Impact's tenant)
- Access to Impact's Azure resources:
  - Resource Group: `rg-Impact-AgenticSystems`
  - Key Vault: `kv-impact-credentials`
  - PostgreSQL: `impact-ai-postgres-v2`
  - Redis: `impact-ai-redis`

### Installation

1. **Clone and setup environment**:
   ```bash
   cd ImpactLangFlow
   cp .env.example .env
   # Edit .env with your actual credentials
   
   pip install -r requirements.txt
   ```

2. **Start the MCP server**:
   ```bash
   cd mcp_server
   python main.py
   # Server starts on http://localhost:8000
   ```

3. **Import flows into LangFlow**:
   - Start LangFlow: `langflow run --host 0.0.0.0 --port 7860`
   - Import each JSON file from `flows/` directory
   - Configure environment variables in LangFlow settings

4. **Launch Streamlit UI**:
   ```bash
   cd streamlit_app
   streamlit run app.py
   # UI available at http://localhost:8501
   ```

## 🎯 Phase Development Plan

### Phase 1: Core Foundation (Current) ✅
- ✅ **Admin & Compliance (Karen)**: Executive assistant with Zoho MCP integration
- ✅ **Recruiting (Katelyn)**: K0-K3 agents for lead processing and outreach
- ✅ **Infrastructure**: Azure PostgreSQL, Redis, Key Vault setup
- ✅ **MCP Server**: FastAPI server with Zoho CRM/Flow integration
- ✅ **Streamlit UI**: ChatGPT-style interface with thread management

### Phase 2: Office Operations (Next)
- **Office Operations (Eileen)**: A1-A12 agents for back-office automation
  - Commission processing with OCR and bank deposits
  - Disbursement authorization workflows
  - Vendor management and facilities
  - License audits and dues processing

### Phase 3: Executive Oversight
- **SOB Supervisor (Kevin)**: S1-S8 agents for executive oversight
  - Unified telemetry collection and KPI computation
  - Daily executive briefs and Q&A
  - Command routing with HITL confirmation
  - Portfolio management and reporting

### Phase 4: Transaction Coordination
- **Additional workflows**: TC processes, DotLoop integration
- **Advanced features**: Cross-system automations, enhanced reporting

## 🤖 Agent Architecture

### SOB Supervisor (Kevin) - S1-S8 Agents
- **S1**: Boot & Routing Orchestrator
- **S2**: Telemetry Normalizer  
- **S3**: KPI & Anomaly Detector
- **S4**: Executive Brief & Q/A
- **S5**: Command Router
- **S6**: Portfolio Assistant
- **S7**: Incident Manager & Escalations
- **S8**: Report Publisher

### Office Operations (Eileen) - A1-A12 Agents
- **A1**: OfficeOps Orchestrator
- **A2**: Communications Triage
- **A3**: Commission Processing
- **A4**: Disbursement Authorization
- **A5**: Vendor & Facilities Management
- **A6**: Task Synchronization
- **A7**: Missing Checks Monitor
- **A8**: Mentor Assignment
- **A9**: License Audit
- **A10**: Dues Processing
- **A11**: Month-End Metrics
- **A12**: Event Projects

### Recruiting (Katelyn) - K0-K3 Agents
- **K0**: KatelynExec Orchestrator
- **K1**: New Agent Intake & Enrichment
- **K2**: Experienced Agent Outreach
- **K3**: Post-Call & Handoff

### Admin & Compliance (Karen)
- **Executive Orchestrator**: Single comprehensive assistant for admin tasks

## 🔧 Configuration

### Environment Variables

Key configuration sections in `.env`:

```bash
# Azure Infrastructure
AZURE_RESOURCE_GROUP=rg-Impact-AgenticSystems
AZURE_KEY_VAULT_NAME=kv-impact-credentials
POSTGRES_URL=postgresql://impactadmin:password@impact-ai-postgres-v2.postgres.database.azure.com:5432/impact_ai
REDIS_URL=rediss://:password@impact-ai-redis.redis.cache.windows.net:6380/0

# LangFlow & MCP
LANGFLOW_URL=http://localhost:7860
MCP_SERVER_URL=http://localhost:8000

# Zoho Integration
ZOHO_CLIENT_ID=your_client_id
ZOHO_CLIENT_SECRET=your_client_secret
ZOHO_REFRESH_TOKEN=your_refresh_token
```

### Azure Resources (Impact Tenant)

Current resources in `rg-Impact-AgenticSystems`:
- **Key Vault**: `kv-impact-credentials` (secrets management)
- **PostgreSQL**: `impact-ai-postgres-v2` (chat & audit persistence)
- **Redis**: `impact-ai-redis` (session memory & caching)

## 🔗 Integrations

The platform integrates with Impact Realty's existing systems:

- **Zoho CRM & Flow**: Primary data and workflow system
- **MLS**: Property data and comparisons
- **Google Workspace**: Calendar, Drive, Gmail
- **Salesmsg**: SMS communications
- **Apify**: Web scraping for agent research
- **DBPR**: Florida license verification
- **BrokerSumo**: Commission and dues processing
- **Twilio**: Backup SMS service

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

Tests cover:
- LangFlow JSON validity
- MCP server endpoints
- Project structure validation
- Schema validation

## 📊 Monitoring & Operations

### Operational Settings
- **Timezone**: America/New_York
- **Quiet Hours**: 19:00 - 08:00 ET
- **Rate Limiting**: 100 requests/minute
- **Session Timeout**: 60 minutes

### Human-in-the-Loop (HITL)
Critical operations require human confirmation:
- Money/compliance actions
- Risk-flagged commands  
- Blueprint transitions
- Bulk data changes

## 🔒 Security

- **Azure Key Vault** for secrets management
- **RBAC** for resource access control
- **SSL/TLS** for all communications
- **OAuth 2.0** for Zoho integration
- **Audit logging** for all operations

## 📈 Scaling & Performance

- **Redis caching** for frequently accessed data
- **Connection pooling** for database efficiency  
- **Async processing** for concurrent operations
- **Rate limiting** to prevent API throttling
- **Background tasks** for long-running operations

## 🛠️ Development

### Adding New Flows
1. Create JSON file in `flows/` directory
2. Follow LangFlow node/edge structure
3. Add environment variable placeholders
4. Update Streamlit UI flow selector
5. Add tests for JSON validity

### MCP Server Extensions
1. Add new endpoints in `main.py`
2. Create Pydantic schemas in `schemas.py`
3. Implement client methods in `zoho_client.py`
4. Add integration tests

## 📞 Support

For technical support or questions:
- Review agent logs in Azure Monitor
- Check LangFlow execution history
- Validate environment variables
- Test MCP endpoint connectivity

---

**Impact Realty AI Platform** - Transforming real estate operations through intelligent automation 🏠🤖