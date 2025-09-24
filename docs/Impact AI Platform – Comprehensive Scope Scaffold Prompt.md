Impact AI Platform – Comprehensive Scope Overview

This document consolidates the scopes for all four functional areas of Impact Realty’s AI platform—Kevin (SOB Supervisor), Eileen (Office Operations), Karen (Admin & Compliance) and Katelyn (Recruiting)—into a single reference. It summarises the goals, agent architectures and primary tools for each area, and defines how these pieces fit together across phases of the project. The initial development focus will be on the Admin & Compliance and Recruiting modules, with subsequent phases extending to the Supervisor and OfficeOps flows.

Supreme Oversight Board (SOB) – Kevin’s Supervisor Agent

The SOB is a LangFlow‑native supervisor that controls all operational flows—recruiting (Katelyn), office operations (Eileen), compliance/admin (Karen) and transaction coordination (Caroline)—while also acting as Kevin’s personal assistant. It ingests telemetry, computes KPIs, detects anomalies, issues alerts and executes cross‑system actions via Zoho CRM, MLS and Google Workspace. All write actions require human‑in‑the‑loop (HITL) confirmation.

Key functions:

Unified telemetry and KPIs: Collect events from all subordinate flows (A1..A17) and external sources; normalise them into a common schema; compute KPIs and trend deltas (e.g., pending DAs, recruiting conversion rates, compliance backlogs). Raise incidents on breaches; aggregate summaries into daily briefs
docs.langflow.org
.

Executive brief & Q/A: Deliver a daily brief at 08:10 ET and handle Kevin’s on‑demand queries with citations to records (CRM IDs, MLS links, calendar events). Unknown answers trigger explicit data‑collection suggestions.

Command router: Parse Kevin’s commands, produce a dry‑run with affected records and risks, and only execute after explicit CONFIRM. Escalate risky actions (money/compliance) for HITL approval.

Portfolio assistant: Maintain Kevin’s commercial real‑estate watchlists, run MLS comparisons, manage tasks and documents, and surface relevant property events.

Reporting: Publish weekly and month‑end dashboards to Google Sheets and Slides; send links via email.

Agent architecture: The SOB is broken into eight sub‑agents (S1–S8), each a LangFlow subgraph with prompts, conditional routers, schedulers, memory and HTTP/MCP calls. S1 orchestrates boot and routing; S2 normalises telemetry; S3 computes KPIs and anomalies; S4 produces the brief and handles Q/A; S5 handles commands; S6 manages portfolio tasks; S7 escalates incidents; and S8 publishes reports
docs.langflow.org
. External integrations include Zoho CRM, MLS, Google Workspace, ticketing (Jira/Helpdesk), Salesmsg/Twilio and optional sources such as DotLoop and BrokerSumo.

Office Operations – Eileen’s Hybrid Workflow

Eileen’s module automates day‑to‑day back‑office operations using LangFlow chains, routers, schedulers and memory. It handles communications triage, commission processing, disbursement authorisations, vendor management, task synchronisation, licence audits and dues cycles. Human review is required for money/compliance actions.

Primary agents (A1–A12):

A1 – OfficeOps Orchestrator: Daily at 08:05 ET, load context from Zoho CRM, Gmail and Calendar and produce a prioritised plan. Dispatch work to other agents only when changes from yesterday are detected.

A2 – Comms Triage: Classify incoming emails and SMS by topic (commissions, DA, vendors, general); auto‑reply when confidence is high; route to the appropriate agent otherwise. Tracks thread state and enforces send‑rate caps.

A3 – Commission Processing: OCR scanned checks, deposit via the bank API, update the CRM commissions module, attach images to Drive and notify the accountant. Prevents double‑deposit via fingerprinting.

A4 – Disbursement Authorisation: Fetch closing documents, cross‑validate numbers, create discrepancy tickets or generate DA PDFs, and update CRM statuses. Requests missing docs and retries periodically.

A5 – Vendor & Facilities: Poll vendor status endpoints, open tickets and schedule on‑site visits when needed. Escalate after repeated failures.

A6 – Task Sync: Bi‑directional sync between CRM tasks and the operations queue; reconcile mismatches.

A7 – Missing Checks Monitor: At 08:00 ET, list all DAs still pending deposit and send follow‑ups until funds arrive.

A8 – Mentor Assignment: On new agent creation, select a mentor, update CRM and send intro emails.

A9 – License Audit: Monthly, fetch DBPR licence statuses, diff against the roster, email expiring agents and generate reports for Drive.

A10 – Dues Processing: On the 1st and 15th, run BrokerSumo charges, parse iTransact confirmations and update CRM statuses.

A11 – Month‑End Metrics: Aggregate dashboards and cycle times, create a PDF and email leadership.

A12 – Event Projects: Manage special events (award ceremonies, holiday parties) by creating projects, sending invites, tracking budgets and distributing collateral.

Each agent is defined as a LangFlow subgraph with prompts, HTTP/MCP calls (e.g., Zoho CRM, bank API, ticketing), schedulers and memory collections. Quiet hours and rate limits (≤40 messages/hour) are enforced at the orchestrator level.

Admin & Compliance – Karen’s Executive Assistant

This module delivers a single “Exec Orchestrator” agent for Karen. It runs on LangFlow and uses a Zoho MCP server plus optional Tavily search to orchestrate admin and compliance tasks. The agent must be idempotent, summarise actions concisely and rely on Zoho MCP flows rather than raw API calls where possible.

Deliverables:

LangFlow flow (karen_exec.json): Contains nodes for ChatInput, Redis Chat Memory, Message History, Supervisor Prompt, Agent (Exec Orchestrator), MCP Tools (Zoho MCP Server), Tavily Search, ChatOutput and Message Store. The wiring mirrors the reference template provided in the SOP (chat input → memory/history → prompt → agent → output/store).

Zoho MCP server: A FastAPI service exposing tools such as flow.run, flow.status, crm.search, crm.upsert, crm.notes.create, crm.tasks.create, blueprint.transition and files.attach. Handles OAuth, argument validation, result normalisation and auditing.

Streamlit app: Provides a ChatGPT‑style UI with a thread list, chat transcript and input bar. Each message call uses the LangFlow run endpoint with a session ID; responses display any record IDs or links returned.

.env example & README: Document environment variables (Zoho, MLS, Google, Salesmsg, Twilio, Postgres, Redis and other keys) and instructions to run the MCP server, import the flow into LangFlow and launch the Streamlit app.

The Exec Orchestrator summarises each turn with up to 10 bullets, preferring Zoho actions over external data, enforcing quiet hours (08:00–19:00 ET) and requiring confirmation for money/compliance actions. Idempotency keys (e.g., contract ID and version) prevent duplicate operations.

Recruiting – Katelyn’s Orchestrator

Katelyn’s workflow orchestrates recruiting from lead ingestion through enrichment, outreach, booking and post‑call handoff. It uses multiple agents (K0–K3) and integrates with ManyChat, Zoho CRM/Flow, Salesmsg, Apify and Tavily. Short‑term state is stored in Redis; longer‑term audit data lives in PostgreSQL.

Agent breakdown:

K0 – KatelynExec Orchestrator: Routes incoming leads to K1 (new agents) or K2 (experienced agents), calls the compliance tool (Aya) as needed and sends KPIs to the SOB. It also generates an 08:10 daily plan and heartbeat pings.

K1 – New Agent Intake & Enrichment: Handles leads with status “null/student/pre‑licence/≤90 days”. Uses DBPR/MLS RAG to enrich data, verifies email, normalises inputs and decides whether to qualify (route to K2), park in nurture or request human review.

K2 – Experienced Agent Outreach: Processes agents ≥2 years or discovered via Apify. Combines Apify scraping, Zoho Social and Salesmsg for outreach. Warm leads are directed to calendar booking; declines are logged with reasons.

K3 – Post‑Call & Handoff: Summarises calls, updates CRM stages, creates onboarding tasks, verifies licences via DBPR and pushes audit data to PostgreSQL. Notifies Eileen or the broker if follow‑up is needed.

Ingress & tools: Leads arrive from ManyChat, Zoho Social, CSV/webhooks, DBPR/MLS RAG feeds, Apify, and manual operator input. GPT is used for social replies; Redis holds thread state; Postgres stores audit logs. Integrations include Zoho CRM, Salesmsg, Google Calendar, Apify, Tavily and the Aya compliance agent.

Phase Plan

Because of the project’s size, development will proceed in phases:

Phase 1 – Admin & Compliance (Karen) and Recruiting (Katelyn):

Build the karen_exec.json flow along with the MCP server and Streamlit app; set up Redis, PostgreSQL and environment variables.

Implement the recruiting orchestrator (recruiting.json) with agents K0–K3, hooking into ManyChat, Zoho CRM, Salesmsg and MLS. Focus on ingestion, enrichment, outreach and handoff without yet wiring to the SOB.

Establish core infrastructure (Azure Postgres/Redis, deployment scripts) and testing harness.

Phase 2 – OfficeOps (Eileen):

Build flows A1–A12, integrating with bank deposit APIs, BrokerSumo, DBPR, ticketing, Calendar and Drive.

Ensure each sub‑agent logs events to the global telemetry store for the SOB.

Phase 3 – Supreme Oversight Board (Kevin):

Develop the SOB supervisor flows S1–S8, normalising events from the recruiting, office and compliance modules, computing KPIs, sending briefs, routing commands and incidents and publishing reports.

Integrate MLS watchlists and property notebooks into the portfolio assistant.

Phase 4 – Transaction Coordination & Additional Roles (e.g., Caroline):

Extend flows to cover TC workflows (DA forms, DotLoop integration), additional recruiting/agent services and cross‑system automations.

By following this phased approach, the project can deliver immediate value (Karen & Katelyn workflows) while progressively layering in the more complex OfficeOps and SOB supervision. Each module remains loosely coupled via MCP/HTTP endpoints and can be developed, tested and deployed independently.

Updated prompt for Claude Code – The prompt below reflects the full magnitude of the project and matches the consolidated scope. It tells Claude to scaffold a Python‑based repository on Azure with separate LangFlow JSON files for each flow (supervisor, office ops, recruiting, admin/compliance), an MCP server, a Streamlit chat UI, and a phased approach to development. You can use this prompt to generate the initial code skeleton.

Prompt for Claude Code (revised)

We’re building a multi‑agent AI platform for Impact Realty on Azure. Use LangFlow (not LangGraph) for orchestration and Streamlit for the chat interface. Our infra includes Azure PostgreSQL, Redis with PGVector, Kubernetes and Azure Key Vault. Generate a complete scaffold that matches the scopes for four flows—SOB (Kevin), OfficeOps (Eileen), Recruiting (Katelyn) and Admin/Compliance (Karen)—with a phased plan starting on the last two. Each flow lives in its own JSON file inside flows/.

Directory layout:

/ (project root)
├── flows/
│   ├── sob_supervisor.json           # Kevin’s S1–S8 supervisor flow
│   ├── office_ops.json              # Eileen’s A1–A12 office operations flow
│   ├── recruiting.json              # Katelyn’s K0–K3 recruiting flow
│   ├── admin_compliance.json        # Karen’s exec/compliance flow
│   └── …                            # future flows (e.g., TC)
├── mcp_server/
│   ├── main.py                      # FastAPI app for Zoho MCP tools
│   ├── zoho_client.py               # OAuth wrapper for Zoho
│   ├── schemas.py                   # Pydantic models for tool args/results
│   └── README.md
├── streamlit_app/
│   ├── app.py                       # ChatGPT‑like UI with thread sidebar
│   ├── lf_client.py                 # Client for LangFlow run endpoint
│   └── db.py                        # Postgres helper functions
├── tests/
│   └── test_basic.py                # Ensure JSON validity and MCP endpoints
├── .env.example                     # Template for all secrets (Zoho, MLS, Google, Salesmsg, Twilio, DB, Redis, etc.)
├── requirements.txt                 # Pinned versions for langflow, streamlit, fastapi, uvicorn, psycopg2, redis, openai, tavily, etc.
└── README.md                        # Run instructions, phase plan and flow descriptions


Environment variables: mirror the full list of keys needed across all modules (Zoho client/secret/refresh, MLS & Tavily keys, Salesmsg/Twilio, Google OAuth, Postgres & Redis URLs, ticketing API, bank/BrokerSumo API, OpenAI, timezone and quiet hours).

LangFlow JSON rules: define the S‑, A‑, K‑ and Exec agents exactly as in the SOPs using LangFlow‑native components (Prompt/LLM, Conditional Router, Scheduler, Memory, HTTP Request); name each node clearly (e.g., “Incident Manager & Escalations”). Do not embed API keys; rely on environment variables.

MCP server: expose zoho.flow.run, zoho.flow.status, zoho.crm.search, zoho.crm.upsert, zoho.crm.notes.create, zoho.crm.tasks.create, zoho.blueprint.transition, and zoho.files.attach. Wrap Zoho’s OAuth in zoho_client.py, implement retries, and audit calls.

Streamlit UI: provide a sidebar listing chat threads, a main transcript pane, and an input bar. For each user message, call POST /v1/run/<flow_id> on the LangFlow server with session_id and show any IDs/links returned in the response metadata.

Phased plan: emphasise that Phase 1 implements the recruiting and admin/compliance flows plus core infrastructure; Phase 2 adds the office operations flow; Phase 3 introduces the SOB supervisor; Phase 4 covers transaction coordination and future modules.

Use this layout and the SOP details to create the skeleton repository. Include placeholders, comments and README guidance, but no business logic.