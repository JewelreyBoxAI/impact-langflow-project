# MCP Server for Impact Realty AI Platform

This FastAPI application provides Model Control Protocol (MCP) tools for Zoho integration, designed to work with LangFlow agents.

## Features

- **Zoho Flow Integration**: Execute and monitor Zoho Flow workflows
- **Zoho CRM Operations**: Search, create, update CRM records
- **Notes & Tasks Management**: Create notes and tasks linked to CRM records
- **Blueprint Transitions**: Execute CRM blueprint state transitions
- **File Attachments**: Attach files to CRM records
- **OAuth Handling**: Automatic token refresh and management
- **Rate Limiting**: Built-in API rate limiting and retry logic
- **Audit Logging**: Comprehensive request/response logging

## API Endpoints

### Health & Status
- `GET /health` - Health check endpoint

### Zoho Flow
- `POST /zoho/flow/run` - Execute a Zoho Flow
- `GET /zoho/flow/status/{execution_id}` - Get flow execution status

### Zoho CRM
- `POST /zoho/crm/search` - Search CRM records
- `POST /zoho/crm/upsert` - Create or update CRM record
- `POST /zoho/crm/notes/create` - Create a note
- `POST /zoho/crm/tasks/create` - Create a task
- `POST /zoho/blueprint/transition` - Execute blueprint transition
- `POST /zoho/files/attach` - Attach file to record

## Environment Variables

Set these environment variables before running:

```bash
# Zoho OAuth
ZOHO_CLIENT_ID=your_zoho_client_id
ZOHO_CLIENT_SECRET=your_zoho_client_secret
ZOHO_REFRESH_TOKEN=your_zoho_refresh_token

# API Configuration
MCP_SERVER_PORT=8000
MCP_SERVER_HOST=0.0.0.0
```

## Installation & Running

1. Install dependencies:
```bash
pip install -r ../requirements.txt
```

2. Set environment variables in `.env` file

3. Run the server:
```bash
python main.py
```

Or using uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Usage with LangFlow

Configure LangFlow HTTP Request nodes to use this MCP server:

```json
{
  "url": "http://localhost:8000/zoho/crm/search",
  "method": "POST",
  "headers": {
    "Authorization": "Bearer your-api-token",
    "Content-Type": "application/json"
  },
  "json": {
    "module": "Leads",
    "criteria": "Email:equals:test@example.com"
  }
}
```

## Authentication

Currently uses bearer token authentication. In production, implement proper JWT or API key validation in the `get_current_user` dependency.

## Rate Limiting

- Default: 100 requests per minute
- Automatic backoff and retry on rate limit hits
- Configurable via environment variables

## Error Handling

- Automatic token refresh on 401 responses
- Exponential backoff retry logic (3 attempts)
- Comprehensive error logging and reporting

## Development

For development with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

For production, consider:
- Using a production WSGI server (gunicorn + uvicorn workers)
- Implementing proper authentication/authorization
- Setting up monitoring and alerting
- Configuring HTTPS/SSL termination
- Database connection pooling for audit logs