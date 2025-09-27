"""
Basic tests for Impact Realty AI Platform
Tests JSON validity and basic MCP endpoints
"""

import json
import pytest
import asyncio
from pathlib import Path
from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_server.main import app
from mcp_server.schemas import CRMSearchRequest

class TestLangFlowJSONFiles:
    """Test LangFlow JSON file validity"""
    
    def test_flows_directory_exists(self):
        """Test that flows directory exists"""
        flows_dir = Path(__file__).parent.parent / "flows"
        assert flows_dir.exists(), "flows/ directory should exist"
        assert flows_dir.is_dir(), "flows/ should be a directory"
    
    def test_sob_supervisor_json_valid(self):
        """Test SOB supervisor flow JSON is valid"""
        flow_path = Path(__file__).parent.parent / "flows" / "sob_supervisor.json"
        assert flow_path.exists(), "sob_supervisor.json should exist"
        
        with open(flow_path, 'r') as f:
            flow_data = json.load(f)
        
        assert flow_data["id"] == "sob_supervisor"
        assert flow_data["name"] == "SOB Supervisor Flow"
        assert "nodes" in flow_data["data"]
        assert "edges" in flow_data["data"]
        
        # Check for key S-agents
        node_ids = [node["id"] for node in flow_data["data"]["nodes"]]
        assert "s1_orchestrator" in node_ids
        assert "s4_brief_qa" in node_ids
        assert "s8_reporting" in node_ids
    
    def test_recruiting_json_valid(self):
        """Test recruiting flow JSON is valid"""
        flow_path = Path(__file__).parent.parent / "flows" / "recruiting.json"
        assert flow_path.exists(), "recruiting.json should exist"
        
        with open(flow_path, 'r') as f:
            flow_data = json.load(f)
        
        assert flow_data["id"] == "recruiting"
        assert flow_data["name"] == "Recruiting Flow"
        
        # Check for key K-agents
        node_ids = [node["id"] for node in flow_data["data"]["nodes"]]
        assert "k0_katelyn_exec" in node_ids
        assert "k1_new_agent_intake" in node_ids
        assert "k2_experienced_outreach" in node_ids
        assert "k3_post_call_handoff" in node_ids
    
    def test_admin_compliance_json_valid(self):
        """Test admin compliance flow JSON is valid"""
        flow_path = Path(__file__).parent.parent / "flows" / "admin_compliance.json"
        assert flow_path.exists(), "admin_compliance.json should exist"
        
        with open(flow_path, 'r') as f:
            flow_data = json.load(f)
        
        assert flow_data["id"] == "karen_exec"
        assert flow_data["name"] == "Karen Executive Flow"
        
        # Check for key nodes
        node_ids = [node["id"] for node in flow_data["data"]["nodes"]]
        assert "chat_input" in node_ids
        assert "exec_orchestrator_agent" in node_ids
        assert "zoho_mcp_tools" in node_ids
    
    def test_office_ops_json_valid(self):
        """Test office operations flow JSON is valid"""
        flow_path = Path(__file__).parent.parent / "flows" / "office_ops.json"
        assert flow_path.exists(), "office_ops.json should exist"
        
        with open(flow_path, 'r') as f:
            flow_data = json.load(f)
        
        assert flow_data["id"] == "office_ops"
        assert flow_data["name"] == "Office Operations Flow"
        
        # Check for key A-agents
        node_ids = [node["id"] for node in flow_data["data"]["nodes"]]
        assert "a1_orchestrator" in node_ids
        assert "a3_commission_processing" in node_ids
        assert "a7_missing_checks" in node_ids
        assert "a11_month_end_metrics" in node_ids


class TestMCPServer:
    """Test MCP server endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_crm_search_endpoint_structure(self, client):
        """Test CRM search endpoint structure (without auth)"""
        # This will fail auth but should show proper error structure
        search_data = {
            "module": "Leads",
            "criteria": "Email:equals:test@example.com",
            "page": 1,
            "per_page": 10
        }
        
        response = client.post("/zoho/crm/search", json=search_data)
        # Should fail with 403/401 due to missing auth, which is expected
        assert response.status_code in [401, 403]


class TestProjectStructure:
    """Test project structure and file organization"""
    
    def test_required_directories_exist(self):
        """Test that all required directories exist"""
        project_root = Path(__file__).parent.parent
        
        required_dirs = [
            "flows",
            "mcp_server", 
            "streamlit_app",
            "tests"
        ]
        
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            assert dir_path.exists(), f"{dir_name}/ directory should exist"
            assert dir_path.is_dir(), f"{dir_name} should be a directory"
    
    def test_required_files_exist(self):
        """Test that required configuration files exist"""
        project_root = Path(__file__).parent.parent
        
        required_files = [
            ".env.example",
            "requirements.txt",
            "mcp_server/main.py",
            "mcp_server/zoho_client.py", 
            "mcp_server/schemas.py",
            "streamlit_app/app.py",
            "streamlit_app/lf_client.py",
            "streamlit_app/db.py"
        ]
        
        for file_path in required_files:
            full_path = project_root / file_path
            assert full_path.exists(), f"{file_path} should exist"
            assert full_path.is_file(), f"{file_path} should be a file"
    
    def test_env_example_has_required_vars(self):
        """Test that .env.example contains required environment variables"""
        env_path = Path(__file__).parent.parent / ".env.example"
        
        with open(env_path, 'r') as f:
            env_content = f.read()
        
        required_vars = [
            "AZURE_KEY_VAULT_NAME",
            "POSTGRES_URL",
            "REDIS_URL", 
            "ZOHO_CLIENT_ID",
            "LANGFLOW_URL",
            "MCP_SERVER_URL",
            "OPENAI_API_KEY"
        ]
        
        for var in required_vars:
            assert var in env_content, f"{var} should be in .env.example"


class TestSchemas:
    """Test Pydantic schemas"""
    
    def test_crm_search_request_schema(self):
        """Test CRM search request schema validation"""
        valid_data = {
            "module": "Leads",
            "criteria": "Email:equals:test@example.com",
            "page": 1,
            "per_page": 50
        }
        
        request = CRMSearchRequest(**valid_data)
        assert request.module == "Leads"
        assert request.criteria == "Email:equals:test@example.com"
        assert request.page == 1
        assert request.per_page == 50
    
    def test_crm_search_request_validation(self):
        """Test CRM search request validation"""
        # Test per_page limit
        with pytest.raises(ValueError):
            CRMSearchRequest(
                module="Leads",
                criteria="test",
                per_page=300  # Exceeds limit of 200
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])