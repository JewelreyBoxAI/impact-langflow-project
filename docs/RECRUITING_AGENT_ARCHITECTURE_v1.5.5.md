# Impact Realty Recruiting Agent - Architecture Summary v1.5.5

**Date:** 2025-09-29
**Flow Version:** 1.5.5 Clean
**Status:** Ready for E2E Testing

---

## 🎯 Executive Summary

The Recruiting Agent (Katelyn) has been completely overhauled to eliminate redundancy, fix breaking HTTP components, and properly leverage Mem0 for conversational memory. The system is now streamlined, production-ready, and uses the **MCP (Model Context Protocol) architecture** for all external integrations.

### Key Improvements in v1.5.5
1. **Removed Custom HTTP Components** - Replaced with MCP Tool (Zoho CRM MCP Server)
2. **Integrated Mem0 Chat Memory** - Proper conversational context and memory persistence
3. **Streamlined Data Flow** - Clear, linear architecture with no redundant paths
4. **PostgreSQL Integration** - Lead storage and database operations
5. **File Upload Support** - Ready for CSV lead imports via UI
6. **Vector Embeddings Pipeline** - OpenAI embeddings for RAG (ready for Tavily Search integration)

---

## 📐 System Architecture

### High-Level Component Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                     RECRUITING AGENT v1.5.5                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐                                                  │
│  │ Chat Input  │──────────────┐                                   │
│  └─────────────┘              │                                   │
│                               ▼                                   │
│  ┌─────────────────────────────────────────┐                     │
│  │         Agent (Katelyn)                 │                     │
│  │  - OpenAI GPT-4o                        │                     │
│  │  - System Prompt Template               │                     │
│  │  - Tool Access (SMS + Zoho + SQL)       │                     │
│  └─────────────────────────────────────────┘                     │
│         │                     │                                   │
│         ▼                     ▼                                   │
│  ┌─────────────┐      ┌──────────────────┐                      │
│  │ Chat Output │      │ Mem0 Chat Memory │                      │
│  └─────────────┘      └──────────────────┘                      │
│         │                     │                                   │
│         └─────────────────────┘                                   │
│                     │                                             │
│                     ▼                                             │
│            Memory Search Results                                  │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                     AGENT TOOLS                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Zoho CRM MCP Server (MCP Protocol)                            │
│     - Lead Creation                                               │
│     - Contact Management                                          │
│     - Deal Pipeline Updates                                       │
│     - Azure Key Vault Integration                                 │
│                                                                     │
│  2. Salesmsg SMS (HTTP API Request)                              │
│     - Send SMS to leads                                           │
│     - Track conversation threads                                  │
│                                                                     │
│  3. PostgreSQL Database (SQL Component)                           │
│     - Store lead information                                      │
│     - Query existing leads                                        │
│     - Track agent interactions                                    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                 RAG PIPELINE (Ready for Extension)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐     ┌────────────┐     ┌──────────────────┐        │
│  │   File   │────▶│ Split Text │────▶│ OpenAI Embeddings│        │
│  │  Upload  │     │  (Chunks)  │     │  (Vector Store)  │        │
│  └──────────┘     └────────────┘     └──────────────────┘        │
│                                                │                   │
│                                                ▼                   │
│                                      [Future: Tavily Search]       │
│                                      [Future: RAG Retrieval]       │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🧠 What is Mem0 and Why We Use It

### What is Mem0?

**Mem0** is an intelligent memory layer for AI applications that provides:
- **Persistent conversational memory** across sessions
- **Semantic search** over past interactions
- **User-specific context** retention
- **Graph-based knowledge storage** (Neo4j optional)
- **Automatic memory summarization** and relevance scoring

### Why We Use Mem0

The recruiting agent needs to:
1. **Remember previous conversations** with leads across multiple sessions
2. **Recall lead preferences**, objections, and interests
3. **Provide personalized follow-ups** based on conversation history
4. **Track agent performance** and conversation outcomes
5. **Enable semantic search** through past interactions

### How We Use Mem0 in v1.5.5

```python
# Mem0 Configuration in Langflow
Component: Mem0 Chat Memory (mem0_chat_memory-I1Q1b)

Inputs:
  - Agent Response (message to ingest)
  - Chat Output (search query for memory retrieval)
  - User ID (unique identifier for lead/conversation)
  - Mem0 API Key (required - see setup below)
  - OpenAI API Key (for embeddings)

Outputs:
  - Memory Instance (persistent memory object)
  - Search Results (relevant past conversations)

Flow:
  1. Agent responds to user query
  2. Response is ingested into Mem0 memory
  3. Chat output triggers memory search
  4. Relevant past conversations are retrieved
  5. Agent uses context for next response
```

### Mem0 Setup Requirements

#### ⚠️ ANTHONY ACTION REQUIRED ⚠️

**Mem0 Account Setup:**

1. **Create Mem0 Account**
   - Go to: https://mem0.ai
   - Sign up for a Mem0 account
   - Choose a plan (Free tier available for development)

2. **Get API Key**
   - Navigate to Dashboard → API Keys
   - Generate a new API key
   - Copy the key (format: `mem0_xxxxx...`)

3. **Store in Azure Key Vault**
   ```bash
   # Add to Key Vault: kv-impact-platform-v2
   az keyvault secret set \
     --vault-name kv-impact-platform-v2 \
     --name MEM0-API-KEY \
     --value "mem0_xxxxxxxxxxxxxxxxxxxxx"
   ```

4. **Configure in Langflow**
   - Open Langflow recruiting flow
   - Click on "Mem0 Chat Memory" component
   - Set `mem0_api_key` to: `@Microsoft.KeyVault(SecretUri=https://kv-impact-platform-v2.vault.azure.net/secrets/MEM0-API-KEY/)`


---

## 🔍 Tavily Search Integration (PENDING)

### What is Tavily Search?

**Tavily** is an AI-powered search API optimized for LLMs and RAG applications:
- **Real-time web search** with structured results
- **Source attribution** and credibility scoring
- **Domain filtering** and customization
- **Built for agentic workflows**

### Why We Need Tavily

The recruiting agent needs to:
1. **Research leads** (company info, social profiles)
2. **Find market data** (real estate trends, comp analysis)
3. **Verify information** (license status, credentials)
4. **Enrich lead profiles** with public data

### Tavily Setup Requirements

#### ⚠️ ANTHONY ACTION REQUIRED ⚠️

**Tavily Account Setup:**

1. **Create Tavily Account**
   - Go to: https://tavily.com
   - Sign up for an API account
   - Choose a plan

2. **Get API Key**
   - Dashboard → API Keys
   - Generate new key

3. **Store in Azure Key Vault**
   ```bash
   az keyvault secret set \
     --vault-name kv-impact-platform-v2 \
     --name TAVILY-API-KEY \
     --value "tvly-xxxxxxxxxxxxxxxxxxxxx"
   ```

4. **Add Tavily Component to Langflow**
   - In Langflow, add "Tavily Search" tool
   - Connect to Agent tools input
   - Configure with API key reference

---

## 🚨 Custom HTTP Components → MCP Tool Migration

### The Problem

**Previous Architecture (v1.5.4 and earlier):**
```
Agent → Custom HTTP Request → Zoho API
  │
  └──→ Custom HTTP Request → Same Zoho API (redundant)
  │
  └──→ Custom HTTP Request → Broken endpoint
```

**Issues:**
1. **Redundant HTTP calls** - Multiple components doing the same thing
2. **No error handling** - HTTP failures broke the entire flow
3. **Hardcoded credentials** - Security risk
4. **No standardization** - Each HTTP component had different auth logic
5. **Breaking changes** - Zoho API updates broke multiple components

### The Solution: MCP (Model Context Protocol)

**New Architecture (v1.5.5):**
```
Agent → MCP Tool (Zoho CRM MCP Server)
          │
          ├─ Standardized protocol
          ├─ Azure Key Vault integration
          ├─ Error handling & retries
          ├─ Tool discovery & schema validation
          └─ Single source of truth
```

**Benefits:**
1. **Single Integration Point** - One MCP server handles all Zoho operations
2. **Automatic Tool Discovery** - MCP exposes available tools to the agent
3. **Type Safety** - JSON schemas validate inputs/outputs
4. **Credential Management** - Azure Key Vault secrets injected at runtime
5. **Error Resilience** - Built-in retry logic and fallback handling
6. **Maintainability** - Update MCP server code once, all flows benefit

### MCP vs HTTP Comparison

| Feature | Custom HTTP Components | MCP Tool |
|---------|----------------------|----------|
| **Code Reuse** | ❌ Copy-paste per flow | ✅ Single server |
| **Error Handling** | ❌ Manual per component | ✅ Built-in |
| **Credential Management** | ❌ Hardcoded or env vars | ✅ Azure Key Vault |
| **Schema Validation** | ❌ Runtime errors | ✅ Compile-time validation |
| **Tool Discovery** | ❌ Manual configuration | ✅ Automatic |
| **Versioning** | ❌ No version control | ✅ Server versioning |
| **Testing** | ❌ Test each HTTP call | ✅ Test MCP server once |
| **Monitoring** | ❌ Per-component logs | ✅ Centralized logs |

### Migration Summary

**Removed:**
- `APIRequest-old1` (Zoho Lead Creation)
- `APIRequest-old2` (Zoho Contact Fetch)
- `APIRequest-old3` (Zoho Deal Update)

**Replaced with:**
- `MCPServer-4b302` (Zoho CRM MCP Server)
  - Exposes: `create_lead`, `get_contact`, `update_deal`, `search_leads`, etc.
  - Auto-discovered by Agent
  - Secured via Azure Key Vault

---

## 💾 Memory Flow and Data Persistence

### Conversation Memory Architecture

```
User Input
    │
    ▼
Agent Processing
    │
    ├──▶ Generate Response
    │         │
    │         ▼
    │    Agent Response ──────────┐
    │                             │
    ▼                             ▼
Chat Output               Mem0 Memory Ingest
    │                             │
    │                             ├─ Store conversation
    │                             ├─ User ID: lead_12345
    │                             └─ Metadata: {source, timestamp, sentiment}
    │
    ▼
Memory Search Query
    │
    ▼
Mem0 Memory Retrieval
    │
    ├─ Semantic search: "Tell me about previous objections"
    ├─ Returns: [conversation_1, conversation_2, ...]
    │
    ▼
Context for Next Agent Response
```

### Mem0 Memory Storage

**What Gets Stored:**
- User messages (lead inputs)
- Agent responses (Katelyn's replies)
- Tool call results (Zoho updates, SMS sent)
- Metadata (timestamp, session_id, lead_id, sentiment)

**Memory Retrieval:**
- **Semantic Search**: "What did this lead say about pricing?"
- **User-Specific**: All conversations for `lead_12345`
- **Temporal**: "Conversations in the last 7 days"
- **Contextual**: Auto-inject relevant memories into agent prompt

---

## 📂 Upload CSV Feature (UI/UX Enhancement)

### Current State

**File Upload Component (File-NE5Ze)** exists in Langflow:
- Supports: CSV, JSON, TXT, PDF, DOCX
- Connects to: Split Text component
- Outputs: Raw file content

### Proposed UI/UX Flow

```
┌─────────────────────────────────────────────────────────┐
│          Frontend: Next.js Upload Component             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  1. User clicks "Upload Lead CSV"                      │
│     └─ Opens file picker                               │
│                                                         │
│  2. CSV validation (client-side)                       │
│     ├─ Check required columns: name, phone, email      │
│     ├─ Validate data formats                           │
│     └─ Preview first 10 rows                           │
│                                                         │
│  3. Upload to backend                                  │
│     POST /api/leads/upload                             │
│     └─ FormData with CSV file                          │
│                                                         │
│  4. Backend processing (FastAPI)                       │
│     ├─ Parse CSV with pandas                           │
│     ├─ Validate each row                               │
│     ├─ Chunk data (100 rows per batch)                 │
│     └─ Send to Langflow File component                 │
│                                                         │
│  5. Langflow RAG Pipeline                              │
│     ├─ File → Split Text → OpenAI Embeddings          │
│     ├─ Store in Vector DB (FAISS/Pinecone)            │
│     └─ Index for semantic search                       │
│                                                         │
│  6. Agent Access                                       │
│     └─ RAG retrieval for "Find leads interested in X" │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### CSV Format Specification

**Required Columns:**
```csv
name,phone,email,source,status,notes
John Doe,555-123-4567,john@example.com,referral,new,Interested in luxury homes
Jane Smith,555-987-6543,jane@example.com,website,contacted,Looking for investment property
```

**Optional Columns:**
- `address`
- `city`
- `state`
- `zip_code`
- `budget`
- `preferred_contact_method`
- `tags` (comma-separated)

### Backend Implementation

**FastAPI Endpoint:**
```python
from fastapi import FastAPI, UploadFile, File
import pandas as pd

app = FastAPI()

@app.post("/api/leads/upload")
async def upload_leads_csv(file: UploadFile = File(...)):
    """
    Upload CSV of leads and process through Langflow RAG pipeline
    """
    # Read CSV
    df = pd.read_csv(file.file)

    # Validate required columns
    required = ['name', 'phone', 'email']
    if not all(col in df.columns for col in required):
        raise ValueError(f"Missing required columns: {required}")

    # Process in batches
    batch_size = 100
    results = []

    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]

        # Send to Langflow File component
        response = await langflow_client.process_file(
            flow_id="recruiting",
            component_id="File-NE5Ze",
            data=batch.to_json(orient='records')
        )

        results.append(response)

    return {
        "status": "success",
        "total_leads": len(df),
        "batches_processed": len(results)
    }
```

### Frontend Component

**React/Next.js Upload Component:**
```typescript
// components/LeadUploadModal.tsx
import { useState } from 'react';
import { uploadLeadCSV } from '@/lib/api';

export function LeadUploadModal() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any[]>([]);

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setFile(file);

    // Parse and preview first 10 rows
    const text = await file.text();
    const rows = text.split('\n').slice(0, 11); // header + 10 rows
    const preview = rows.map(row => row.split(','));
    setPreview(preview);
  };

  const handleUpload = async () => {
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    const result = await uploadLeadCSV(formData);
    console.log('Upload result:', result);
  };

  return (
    <div className="modal">
      <input type="file" accept=".csv" onChange={handleFileSelect} />

      {preview.length > 0 && (
        <div className="preview">
          <h3>Preview (first 10 rows):</h3>
          <table>
            <thead>
              <tr>
                {preview[0].map((col, i) => <th key={i}>{col}</th>)}
              </tr>
            </thead>
            <tbody>
              {preview.slice(1).map((row, i) => (
                <tr key={i}>
                  {row.map((cell, j) => <td key={j}>{cell}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <button onClick={handleUpload}>Upload {file?.name}</button>
    </div>
  );
}
```

---

## 🗺️ E2E Live Testing Roadmap

### Phase 1: Prerequisites Setup (Week 1)

#### 1.1 Mem0 Account & API Key
- [ ] Create Mem0 account (Anthony)
- [ ] Generate Mem0 API key
- [ ] Store in Azure Key Vault: `MEM0-API-KEY`
- [ ] Update Langflow component configuration

#### 1.2 Tavily Search Account & API Key
- [ ] Create Tavily account (Anthony)
- [ ] Generate Tavily API key
- [ ] Store in Azure Key Vault: `TAVILY-API-KEY`
- [ ] Add Tavily Search tool to Langflow

#### 1.3 Environment Configuration
- [ ] Verify all Azure Key Vault secrets exist:
  - `ZOHO-CLIENT-ID`
  - `ZOHO-CLIENT-SECRET`
  - `ZOHO-REFRESH-TOKEN`
  - `ZOHO-ACCESS-TOKEN`
  - `OPENAI-API-KEY`
  - `SALESMSG-API-KEY`
  - `MEM0-API-KEY`
  - `TAVILY-API-KEY`
- [ ] Update `.env` files with Key Vault references
- [ ] Test secret retrieval from Key Vault

---

### Phase 2: Infrastructure Validation (Week 1-2)

#### 2.1 Langflow Deployment
- [ ] Deploy Langflow v1.5.5 clean flow to Azure
- [ ] Verify all components load without errors
- [ ] Test component connections in Langflow UI
- [ ] Run Langflow health check: `http://localhost:7860/health`

#### 2.2 Database Validation
- [ ] Test PostgreSQL connection from Langflow
- [ ] Verify `leads` table schema exists
- [ ] Run test INSERT query
- [ ] Run test SELECT query

#### 2.3 MCP Server Validation
- [ ] Start Zoho CRM MCP Server
  ```bash
  cd MCPServers/zoho-crm-mcp-server
  python -m zoho_crm_mcp.server
  ```
- [ ] Verify MCP server responds to tool discovery
- [ ] Test individual MCP tools:
  - [ ] `create_lead`
  - [ ] `get_contact`
  - [ ] `search_leads`
- [ ] Check Azure Key Vault secret injection

#### 2.4 External API Tests
- [ ] Test Salesmsg SMS API
  - [ ] Send test SMS
  - [ ] Verify delivery status
- [ ] Test Zoho CRM API via MCP
  - [ ] Create test lead
  - [ ] Fetch test lead
  - [ ] Update test lead
- [ ] Test OpenAI API
  - [ ] Generate test embedding
  - [ ] Verify embedding dimensions

---

### Phase 3: Component Testing (Week 2)

#### 3.1 Mem0 Memory Tests
- [ ] Test memory ingestion
  - [ ] Send test message to agent
  - [ ] Verify message stored in Mem0
  - [ ] Check Mem0 dashboard for entry
- [ ] Test memory retrieval
  - [ ] Query: "What did I say earlier?"
  - [ ] Verify agent retrieves correct context
- [ ] Test user-specific memory
  - [ ] Create conversations for user_1
  - [ ] Create conversations for user_2
  - [ ] Verify no cross-user memory leakage

#### 3.2 Agent Tool Usage Tests
- [ ] Test SMS tool
  - [ ] Agent instruction: "Send SMS to 555-123-4567"
  - [ ] Verify SMS sent via Salesmsg API
  - [ ] Check agent receives confirmation
- [ ] Test Zoho CRM tool
  - [ ] Agent instruction: "Create lead for John Doe"
  - [ ] Verify lead created in Zoho
  - [ ] Check lead data accuracy
- [ ] Test PostgreSQL tool
  - [ ] Agent instruction: "Store this lead in database"
  - [ ] Verify database INSERT
  - [ ] Query database to confirm

#### 3.3 RAG Pipeline Tests
- [ ] Test file upload
  - [ ] Upload test CSV (5 sample leads)
  - [ ] Verify Split Text processing
  - [ ] Check OpenAI Embeddings generation
- [ ] Test semantic search
  - [ ] Query: "Find leads interested in luxury homes"
  - [ ] Verify correct leads retrieved
  - [ ] Check relevance scoring

---

### Phase 4: End-to-End Workflow Tests (Week 3)

#### 4.1 New Lead Conversation Flow
**Test Scenario:** New lead initiates conversation

- [ ] **Step 1:** User sends message: "Hi, I'm looking for a 3BR home in Austin"
- [ ] **Step 2:** Agent responds with:
  - Greeting
  - Qualification questions
  - Stores conversation in Mem0
- [ ] **Step 3:** User provides budget: "$500k-$600k"
- [ ] **Step 4:** Agent:
  - Creates lead in Zoho CRM
  - Stores lead in PostgreSQL
  - Sends confirmation SMS
  - Updates Mem0 memory
- [ ] **Step 5:** Verify:
  - Lead exists in Zoho
  - Lead exists in PostgreSQL
  - SMS sent successfully
  - Mem0 memory contains conversation
  - Agent can recall lead details in next message

#### 4.2 Returning Lead Conversation Flow
**Test Scenario:** Existing lead returns for follow-up

- [ ] **Step 1:** User sends message: "Any updates on properties?"
- [ ] **Step 2:** Agent:
  - Retrieves conversation history from Mem0
  - Recalls lead preferences ($500k-$600k, 3BR, Austin)
  - Queries Zoho for matching properties
- [ ] **Step 3:** Agent responds with:
  - "Welcome back! I remember you're looking for..."
  - List of matching properties
- [ ] **Step 4:** User shows interest in property
- [ ] **Step 5:** Agent:
  - Updates lead status in Zoho
  - Schedules showing via Zoho Calendar
  - Sends SMS confirmation
  - Stores interaction in Mem0

#### 4.3 Bulk Lead Upload Flow
**Test Scenario:** Upload CSV with 50 leads

- [ ] **Step 1:** User uploads `leads_sample.csv`
- [ ] **Step 2:** Frontend validates CSV
- [ ] **Step 3:** Backend processes CSV in batches
- [ ] **Step 4:** Langflow RAG pipeline:
  - Splits text into chunks
  - Generates embeddings
  - Stores in vector database
- [ ] **Step 5:** Agent can now:
  - Query: "Show me leads from referrals"
  - Query: "Find leads with budget > $1M"
  - Query: "Leads interested in investment properties"

#### 4.4 Multi-Tool Workflow
**Test Scenario:** Complex lead interaction using multiple tools

- [ ] **Step 1:** Lead asks: "Can you create my profile and text me details?"
- [ ] **Step 2:** Agent plan:
  1. Ask for lead information
  2. Create lead in Zoho (MCP Tool)
  3. Store in PostgreSQL (SQL Tool)
  4. Send SMS confirmation (SMS Tool)
  5. Store conversation (Mem0)
- [ ] **Step 3:** Execute plan
- [ ] **Step 4:** Verify all tools executed successfully
- [ ] **Step 5:** Check logs for errors

---

### Phase 5: Performance & Load Testing (Week 3-4)

#### 5.1 Concurrency Tests
- [ ] Test 10 concurrent conversations
- [ ] Test 50 concurrent conversations
- [ ] Test 100 concurrent conversations
- [ ] Measure:
  - Response time (target: <2s)
  - Memory usage
  - CPU usage
  - Database connection pool
  - API rate limits

#### 5.2 Mem0 Performance
- [ ] Test memory retrieval speed
  - [ ] 100 memories: <500ms
  - [ ] 1,000 memories: <1s
  - [ ] 10,000 memories: <2s
- [ ] Test memory ingestion rate
  - [ ] 100 messages/sec
- [ ] Test semantic search accuracy
  - [ ] Precision: >80%
  - [ ] Recall: >70%

#### 5.3 RAG Performance
- [ ] Test embedding generation time
  - [ ] 100 chunks: <5s
  - [ ] 1,000 chunks: <30s
- [ ] Test vector search time
  - [ ] 10k vectors: <100ms
  - [ ] 100k vectors: <500ms

---

### Phase 6: Error Handling & Edge Cases (Week 4)

#### 6.1 API Failure Tests
- [ ] Simulate Zoho API down
  - [ ] Verify graceful degradation
  - [ ] Check fallback behavior
  - [ ] Verify error message to user
- [ ] Simulate Salesmsg API down
  - [ ] Verify retry logic
  - [ ] Check queuing mechanism
- [ ] Simulate OpenAI API down
  - [ ] Verify fallback embedding model
  - [ ] Check cached embeddings

#### 6.2 Mem0 Failure Tests
- [ ] Simulate Mem0 API timeout
  - [ ] Verify agent continues without memory
  - [ ] Check warning logged
- [ ] Test memory search with no results
  - [ ] Verify agent handles gracefully
  - [ ] Check fallback to stateless conversation

#### 6.3 Data Validation Tests
- [ ] Invalid phone number format
  - [ ] Verify validation error
  - [ ] Check user-friendly error message
- [ ] Invalid email format
  - [ ] Verify validation error
- [ ] Duplicate lead detection
  - [ ] Verify Zoho deduplication
  - [ ] Check merge strategy

---

### Phase 7: Security & Compliance (Week 4-5)

#### 7.1 Credential Security
- [ ] Verify no hardcoded secrets in code
- [ ] Verify Azure Key Vault usage
- [ ] Test Key Vault access permissions
- [ ] Audit Key Vault access logs

#### 7.2 Data Privacy
- [ ] Verify PII encryption at rest
- [ ] Test HTTPS enforcement
- [ ] Check GDPR compliance:
  - [ ] Right to be forgotten
  - [ ] Data export capability
  - [ ] Consent management

#### 7.3 Access Control
- [ ] Test role-based access
  - [ ] Admin: Full access
  - [ ] Agent: Limited access
  - [ ] Read-only: View-only
- [ ] Test session management
  - [ ] Session timeout
  - [ ] Concurrent session handling

---

### Phase 8: Monitoring & Observability (Week 5)

#### 8.1 Logging Setup
- [ ] Configure Azure Application Insights
- [ ] Set up log aggregation
- [ ] Define log levels:
  - ERROR: Critical failures
  - WARN: Degraded performance
  - INFO: Normal operations
  - DEBUG: Detailed traces

#### 8.2 Metrics & Alerts
- [ ] Define key metrics:
  - [ ] Conversation response time
  - [ ] Tool success rate
  - [ ] Memory retrieval latency
  - [ ] API error rate
- [ ] Set up alerts:
  - [ ] Response time >3s
  - [ ] Error rate >5%
  - [ ] API quota exceeded
  - [ ] Database connection failures

#### 8.3 Dashboards
- [ ] Create Grafana dashboards:
  - [ ] Real-time conversation metrics
  - [ ] Tool usage statistics
  - [ ] Memory performance
  - [ ] API health status

---

### Phase 9: User Acceptance Testing (Week 5-6)

#### 9.1 Internal Testing
- [ ] Anthony tests recruiting workflows
- [ ] Katelyn tests lead management
- [ ] Record feedback and issues

#### 9.2 Pilot Testing
- [ ] Select 5 pilot users
- [ ] Provide training and documentation
- [ ] Collect feedback:
  - [ ] Usability issues
  - [ ] Feature requests
  - [ ] Performance complaints

#### 9.3 Iteration
- [ ] Fix critical bugs
- [ ] Implement high-priority feedback
- [ ] Retest with pilot users

---

### Phase 10: Production Deployment (Week 6)

#### 10.1 Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Security audit complete
- [ ] Performance benchmarks met
- [ ] Documentation complete:
  - [ ] User guide
  - [ ] Admin guide
  - [ ] API documentation
  - [ ] Runbook for incidents

#### 10.2 Deployment
- [ ] Deploy to production environment
- [ ] Run smoke tests
- [ ] Monitor for 24 hours
- [ ] Verify:
  - [ ] All services healthy
  - [ ] No critical errors
  - [ ] Performance within SLA

#### 10.3 Go-Live
- [ ] Announce to users
- [ ] Provide support channel
- [ ] Monitor closely for 1 week
- [ ] Collect early feedback

---

## 📊 Success Criteria

### Functional Requirements
- [ ] Agent responds to user queries within 2 seconds
- [ ] Memory persists across sessions
- [ ] All tools (SMS, Zoho, SQL) work reliably
- [ ] CSV upload processes without errors
- [ ] RAG retrieval returns relevant results

### Performance Requirements
- [ ] Handle 100 concurrent users
- [ ] 99.9% uptime
- [ ] <1% error rate
- [ ] Memory retrieval <500ms
- [ ] Embedding generation <5s per 100 chunks

### Security Requirements
- [ ] All secrets in Azure Key Vault
- [ ] HTTPS enforced
- [ ] No PII in logs
- [ ] GDPR compliant
- [ ] Access control working

---

## 🛠️ Troubleshooting Guide

### Common Issues

#### Issue: Mem0 Memory Not Persisting
**Symptoms:** Agent doesn't remember previous conversations

**Diagnosis:**
1. Check Mem0 API key is set
2. Verify `user_id` is consistent across sessions
3. Check Mem0 dashboard for entries

**Fix:**
```python
# Verify Mem0 configuration
mem0_memory = Memory(api_key="mem0_xxxxx")
result = mem0_memory.get_all(user_id="test_user")
print(result)  # Should show stored memories
```

#### Issue: MCP Tool Not Responding
**Symptoms:** Agent says "Tool not found" or times out

**Diagnosis:**
1. Check MCP server is running
2. Verify Azure Key Vault secrets
3. Test MCP tool directly

**Fix:**
```bash
# Restart MCP server
cd MCPServers/zoho-crm-mcp-server
python -m zoho_crm_mcp.server

# Test tool
curl http://localhost:3000/tools
```

#### Issue: RAG Not Retrieving Results
**Symptoms:** Agent can't find uploaded lead data

**Diagnosis:**
1. Check if embeddings were generated
2. Verify vector store is populated
3. Test semantic search query

**Fix:**
```python
# Check vector store
from langflow.components.vectorstores import FAISS
vectorstore = FAISS.load_local("path/to/index")
results = vectorstore.similarity_search("test query", k=5)
print(results)
```

---

## 📚 Additional Resources

- **Mem0 Documentation:** https://docs.mem0.ai
- **Tavily Search Docs:** https://docs.tavily.com
- **MCP Protocol Spec:** https://modelcontextprotocol.io
- **Langflow Docs:** https://docs.langflow.org
- **Azure Key Vault:** https://learn.microsoft.com/azure/key-vault

---

## 🏁 Next Steps

1. **Anthony:** Set up Mem0 and Tavily accounts (this week)
2. **Anthony:** Store API keys in Azure Key Vault (this week)
3. **Team:** Review this architecture document (this week)
4. **Team:** Begin Phase 1 of E2E testing roadmap (next week)
5. **Team:** Schedule weekly checkpoint meetings

---

**Document Version:** 1.0
**Last Updated:** 2025-09-29
**Author:** Claude (Impact Realty AI Development Team)
**Status:** Ready for Review