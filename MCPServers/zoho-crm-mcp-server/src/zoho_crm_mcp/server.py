from mcp.server.fastmcp import FastMCP
import requests
import json
import os
import time
import base64
import hashlib
import secrets
import urllib.parse
from dotenv import load_dotenv
from pathlib import Path
from typing import Any

# Load environment variables from .env.local
env_path = Path(__file__).parent.parent.parent / ".env.local"
load_dotenv(env_path)

mcp = FastMCP("Zoho CRM MCP Server")

# Get credentials from environment variables
ZOHO_CLIENT_ID = os.getenv("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.getenv("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.getenv("ZOHO_REFRESH_TOKEN", "Generate-from-OAuth")
ZOHO_ACCESS_TOKEN = os.getenv("ZOHO_ACCESS_TOKEN", "Generate-from-OAuth")
ZOHO_CRM_BASE_URL = os.getenv("ZOHO_CRM_BASE_URL", "https://www.zohoapis.com/crm/v2")
ZOHO_AUTH_URL = os.getenv("ZOHO_AUTH_URL", "https://accounts.zoho.com/oauth/v2/token")
ZOHO_REDIRECT_URL = os.getenv("ZOHO_REDIRECT_URL", "http://127.0.0.1:8787/oauth")
ZOHO_ADMIN_EMAIL = os.getenv("ZOHO_ADMIN_EMAIL")
ZOHO_LOGIN_PW = os.getenv("ZOHO_LOGIN_PW")

# Token persistence file
TOKEN_FILE = Path(__file__).parent.parent.parent / ".tokens.json"

# Global variables to store current tokens
current_access_token = None
current_refresh_token = None

def load_tokens():
    """Load tokens from persistent storage"""
    global current_access_token, current_refresh_token

    try:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                current_access_token = tokens.get('access_token')
                current_refresh_token = tokens.get('refresh_token')
                return True
    except Exception as e:
        print(f"Failed to load tokens: {e}")

    # Fallback to environment variables
    if ZOHO_ACCESS_TOKEN != "Generate-from-OAuth":
        current_access_token = ZOHO_ACCESS_TOKEN
    if ZOHO_REFRESH_TOKEN != "Generate-from-OAuth":
        current_refresh_token = ZOHO_REFRESH_TOKEN

    return current_access_token is not None

def save_tokens(access_token=None, refresh_token=None, expires_in=None):
    """Save tokens to persistent storage"""
    global current_access_token, current_refresh_token

    if access_token:
        current_access_token = access_token
    if refresh_token:
        current_refresh_token = refresh_token

    token_data = {
        "access_token": current_access_token,
        "refresh_token": current_refresh_token,
        "created_at": int(time.time()),
        "expires_in": expires_in or 3600
    }

    try:
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        print("Tokens saved successfully")
    except Exception as e:
        print(f"Failed to save tokens: {e}")

def refresh_access_token():
    """Refresh the Zoho access token using refresh token"""
    global current_access_token

    if not current_refresh_token:
        return {"error": "No refresh token available. Need to complete OAuth setup first."}

    data = {
        "refresh_token": current_refresh_token,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }

    try:
        response = requests.post(ZOHO_AUTH_URL, data=data)
        if response.status_code == 200:
            token_data = response.json()
            current_access_token = token_data.get("access_token")
            # Save the new access token (refresh token remains the same)
            save_tokens(access_token=current_access_token, expires_in=token_data.get("expires_in"))
            return {"success": True, "token": current_access_token}
        else:
            return {"error": f"Token refresh failed: {response.text}"}
    except Exception as e:
        return {"error": f"Token refresh error: {str(e)}"}

def generate_oauth_tokens():
    """Generate OAuth tokens using Self-Client approach"""

    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        return {"error": "Missing client credentials"}

    # For Zoho Self-Client, we can use the client credentials grant
    # This is the most autonomous approach for server-to-server communication
    data = {
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "client_credentials",
        "scope": "ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.org.ALL"
    }

    try:
        response = requests.post(ZOHO_AUTH_URL, data=data)
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")  # May not be provided for client_credentials
            expires_in = token_data.get("expires_in", 3600)

            # Save tokens
            save_tokens(access_token=access_token, refresh_token=refresh_token, expires_in=expires_in)

            return {
                "success": True,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_in": expires_in
            }
        else:
            # If client_credentials fails, we might need authorization_code flow
            return {"error": f"OAuth token generation failed: {response.text}", "needs_authorization_code": True}
    except Exception as e:
        return {"error": f"OAuth generation error: {str(e)}"}

def ensure_valid_token():
    """Ensure we have a valid access token, generate if needed"""
    global current_access_token, current_refresh_token

    # Try to load existing tokens first
    if not current_access_token:
        load_tokens()

    # If we have a refresh token but no access token, try to refresh
    if current_refresh_token and not current_access_token:
        refresh_result = refresh_access_token()
        if refresh_result.get("success"):
            return True

    # If we still don't have tokens, try to generate them
    if not current_access_token:
        print("No valid tokens found. Attempting to generate OAuth tokens...")
        oauth_result = generate_oauth_tokens()

        if oauth_result.get("success"):
            print("OAuth tokens generated successfully!")
            return True
        else:
            print(f"OAuth generation failed: {oauth_result.get('error')}")
            if oauth_result.get("needs_authorization_code"):
                print("This Zoho app may require authorization code flow with user consent.")
                print("Consider updating your Zoho app to allow Self-Client or Server-based authentication.")
            return False

    return True

def get_auth_headers():
    """Get authorization headers with current token"""
    if not current_access_token:
        ensure_valid_token()

    return {
        "Authorization": f"Zoho-oauthtoken {current_access_token}",
        "Content-Type": "application/json"
    }

def make_authenticated_request(method, url, **kwargs):
    """Make an authenticated request with automatic token refresh on 401"""
    headers = get_auth_headers()
    kwargs['headers'] = headers

    response = requests.request(method, url, **kwargs)

    # If unauthorized, try to refresh token and retry once
    if response.status_code == 401:
        refresh_result = refresh_access_token()
        if refresh_result.get("success"):
            headers = get_auth_headers()
            kwargs['headers'] = headers
            response = requests.request(method, url, **kwargs)

    return response


ZOHO_MODULES = [
    "Leads",
    "Accounts",
    "Contacts",
    "Deals",
    "Events",
    "Tasks",
    "Calls",
    "users"
]

@mcp.tool()
def get_module_data(ctx, module_name: str = None, limit: int = 5):
    """
    Fetch data from Zoho CRM modules with essential fields only

    Args:
        module_name: Specific module name (e.g., 'Contacts', 'Leads')
        limit: Number of records to fetch (default 5, max 10)
    """
    
    # Strict limit to prevent token explosion
    limit = min(limit, 10)
    
    # Define essential fields per module
    field_mapping = {
        "Leads": "id,Full_Name,First_Name,Last_Name,Email,Phone,Lead_Status,Lead_Source,Company,Owner",
        "Contacts": "id,Full_Name,First_Name,Last_Name,Email,Phone,Account_Name,Owner",
        "Deals": "id,Deal_Name,Amount,Stage,Closing_Date,Owner",
        "Accounts": "id,Account_Name,Phone,Website,Annual_Revenue,Owner",
    }
    
    fields = field_mapping.get(module_name, "id,Full_Name,Email,Phone,Owner")

    if module_name:
        url = f"{ZOHO_CRM_BASE_URL}/{module_name}"
        params = {
            "fields": fields,
            "per_page": limit
        }
        response = make_authenticated_request("GET", url, params=params)
        
        if response.status_code == 200:
            data = response.json().get("data", [])
            return {
                "status": "success",
                "module": module_name,
                "count": len(data),
                "fields_returned": fields,
                "data": data
            }
        else:
            return {
                "status": "error",
                "module": module_name,
                "message": response.text,
                "code": response.status_code
            }
    else:
        return {
            "status": "error",
            "message": "module_name is required"
        }

@mcp.tool()
def get_available_modules(ctx):
    """Get list of all available modules in Zoho CRM"""

    url = f"{ZOHO_CRM_BASE_URL}/settings/modules"
    response = make_authenticated_request("GET", url)
    
    if response.status_code == 200:
        modules = response.json().get("modules", [])
        return {
            "status": "success",
            "count": len(modules),
            "modules": [module["api_name"] for module in modules]
        }
    else:
        return {
            "status": "error",
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def search_records(ctx, module_name: str, search_criteria: str):
    """
    Search for records in a specific module

    Args:
        module_name: Module to search in (e.g., 'Contacts', 'Leads')
        search_criteria: Search query in format '(FieldName:operator:value)'
                        Operators: equals, starts_with, contains
                        Example: '(Last_Name:equals:Smith)' or '(Email:contains:gmail.com)'
    """
    
    # Auto-wrap criteria if user didn't include parentheses
    if not search_criteria.startswith('('):
        # Try to parse and fix common formats
        if ':' in search_criteria:
            parts = search_criteria.split(':')
            if len(parts) == 2:
                # User sent "Last_Name:Barthel" - add equals operator
                search_criteria = f"({parts[0]}:equals:{parts[1]})"
            elif len(parts) == 3:
                # User sent "Last_Name:equals:Barthel" - just add parentheses
                search_criteria = f"({search_criteria})"

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}/search"
    
    # Limit fields to essential ones
    field_mapping = {
        "Leads": "id,Full_Name,First_Name,Last_Name,Email,Phone,Lead_Status,Owner",
        "Contacts": "id,Full_Name,First_Name,Last_Name,Email,Phone,Owner",
    }
    fields = field_mapping.get(module_name, "id,Full_Name,Email,Phone")
    
    params = {
        "criteria": search_criteria,
        "fields": fields
    }

    response = make_authenticated_request("GET", url, params=params)
    
    # Handle 204 No Content - means no records found (this is success, not error)
    if response.status_code == 204:
        return {
            "status": "success",
            "module": module_name,
            "count": 0,
            "search_criteria": search_criteria,
            "message": "No records found matching the search criteria",
            "data": []
        }
    elif response.status_code == 200:
        data = response.json().get("data", [])
        return {
            "status": "success",
            "module": module_name,
            "count": len(data),
            "search_criteria": search_criteria,
            "data": data
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code,
            "hint": "Use format: (FieldName:equals:Value) or (FieldName:contains:Value)"
        }

@mcp.tool()
def create_record(ctx, module_name: str, record_data: Any):
    """
    Create a new record in a specific module

    Args:
        module_name: Module to create record in (e.g., 'Contacts', 'Leads')
        record_data: Dictionary or JSON string containing the record fields and values
                    Example: {"First_Name": "John", "Last_Name": "Doe", "Email": "john@example.com"}
    """
    
    # Handle both string and dict
    if isinstance(record_data, str):
        try:
            data_dict = json.loads(record_data)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in record_data: {str(e)}"
            }
    elif isinstance(record_data, dict):
        data_dict = record_data
    else:
        return {
            "status": "error",
            "message": f"Invalid record_data type: {type(record_data)}"
        }
    
    # Validate not empty
    if not data_dict:
        return {
            "status": "error",
            "message": "record_data is empty! Cannot create with no fields."
        }

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}"

    # Wrap the record data in the required format
    payload = {
        "data": [data_dict]
    }

    # FIX: Use json= parameter instead of data=json.dumps()
    response = make_authenticated_request("POST", url, json=payload)
    
    if response.status_code == 201:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "message": "Record created successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def update_record(ctx, module_name: str, record_id: str, record_data: Any):
    """
    Update an existing record in a specific module

    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to update
        record_data: Dictionary or JSON string containing the fields to update
                    Example: {"First_Name": "Jane", "Email": "jane@example.com"}
    """
    
    # Handle both string and dict
    if isinstance(record_data, str):
        try:
            data_dict = json.loads(record_data)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in record_data: {str(e)}"
            }
    elif isinstance(record_data, dict):
        data_dict = record_data
    else:
        return {
            "status": "error",
            "message": f"Invalid record_data type: {type(record_data)}"
        }
    
    # Validate not empty
    if not data_dict:
        return {
            "status": "error",
            "message": "record_data is empty! Cannot update with no fields.",
            "received_type": str(type(record_data)),
            "received_value": str(record_data)
        }

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}/{record_id}"
    payload = {"data": [data_dict]}

    response = make_authenticated_request("PUT", url, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "record_id": record_id,
            "message": "Record updated successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "record_id": record_id,
            "message": response.text,
            "code": response.status_code
        }
    
@mcp.tool()
def delete_record(ctx, module_name: str, record_id: str):
    """
    Delete a record from a specific module

    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to delete
    """

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}/{record_id}"

    response = make_authenticated_request("DELETE", url)
    
    if response.status_code == 200:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "record_id": record_id,
            "message": "Record deleted successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "record_id": record_id,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def bulk_create_records(ctx, module_name: str, records_data: Any):
    """
    Create multiple records in a specific module

    Args:
        module_name: Module to create records in (e.g., 'Contacts', 'Leads')
        records_data: List of dictionaries or JSON string containing record data
                     Example: [{"First_Name": "John", "Last_Name": "Doe"}, {"First_Name": "Jane", "Last_Name": "Smith"}]
    """
    
    # Handle both string and list
    if isinstance(records_data, str):
        try:
            data_list = json.loads(records_data)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in records_data: {str(e)}"
            }
    elif isinstance(records_data, list):
        data_list = records_data
    else:
        return {
            "status": "error",
            "message": f"Invalid records_data type: {type(records_data)}"
        }
    
    # Validate not empty
    if not data_list:
        return {
            "status": "error",
            "message": "records_data is empty! Cannot create with no records."
        }

    # Zoho CRM allows up to 100 records per API call
    if len(data_list) > 100:
        return {
            "status": "error",
            "message": "Maximum 100 records allowed per bulk operation"
        }

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}"
    payload = {
        "data": data_list
    }

    response = make_authenticated_request("POST", url, json=payload)
    
    if response.status_code == 201:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "message": f"{len(data_list)} records created successfully",
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def get_record_by_id(ctx, module_name: str, record_id: str):
    """
    Get a specific record by its ID

    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to retrieve
    """

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}/{record_id}"

    response = make_authenticated_request("GET", url)
    
    if response.status_code == 200:
        result = response.json()
        data = result.get("data", [])
        return {
            "status": "success",
            "module": module_name,
            "record_id": record_id,
            "data": data[0] if data else None
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "record_id": record_id,
            "message": response.text,
            "code": response.status_code
        }


@mcp.tool()
def set_refresh_token(ctx, refresh_token: str):
    """
    Manually set a long-lived refresh token for autonomous operation

    Args:
        refresh_token: A valid Zoho refresh token obtained through OAuth flow
    """
    global current_refresh_token

    try:
        # Save the refresh token
        current_refresh_token = refresh_token
        save_tokens(refresh_token=refresh_token)

        # Try to generate a new access token immediately
        refresh_result = refresh_access_token()

        if refresh_result.get("success"):
            return {
                "status": "success",
                "message": "Refresh token set successfully and access token generated",
                "access_token": current_access_token[:20] + "..." if current_access_token else "None"
            }
        else:
            return {
                "status": "error",
                "message": f"Refresh token saved but failed to generate access token: {refresh_result.get('error')}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to set refresh token: {str(e)}"
        }

@mcp.tool()
def get_token_status(ctx):
    """
    Get the current status of OAuth tokens and authentication
    """
    return {
        "access_token_available": current_access_token is not None,
        "access_token_preview": current_access_token[:20] + "..." if current_access_token else "None",
        "refresh_token_available": current_refresh_token is not None,
        "refresh_token_preview": current_refresh_token[:20] + "..." if current_refresh_token else "None",
        "token_file_exists": TOKEN_FILE.exists(),
        "client_id": ZOHO_CLIENT_ID[:10] + "..." if ZOHO_CLIENT_ID else "Not set",
        "client_secret_set": bool(ZOHO_CLIENT_SECRET),
        "ready_for_api_calls": current_access_token is not None
    }

@mcp.tool()
def test_zoho_connection(ctx):
    """
    Test the connection to Zoho CRM API with current tokens
    """
    try:
        # Ensure we have valid tokens
        if not ensure_valid_token():
            return {
                "status": "error",
                "message": "No valid tokens available. Cannot test connection."
            }

        # Use /users endpoint instead - we have ZohoCRM.users.ALL scope
        url = f"{ZOHO_CRM_BASE_URL}/users"
        params = {"type": "ActiveUsers", "per_page": 1}
        response = make_authenticated_request("GET", url, params=params)

        if response.status_code == 200:
            user_data = response.json()
            users = user_data.get("users", [])
            return {
                "status": "success",
                "message": "Successfully connected to Zoho CRM",
                "user_count": len(users),
                "first_user": users[0].get("full_name") if users else "No users found",
                "api_base_url": ZOHO_CRM_BASE_URL
            }
        else:
            return {
                "status": "error",
                "message": f"Connection test failed: {response.status_code} - {response.text}"
            }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Connection test error: {str(e)}"
        }

@mcp.tool()
def get_users(ctx, user_type: str = "AllUsers"):
    """
    Get all users in the Zoho CRM organization

    Args:
        user_type: Type of users to fetch (AllUsers, ActiveUsers, DeactiveUsers, ConfirmedUsers)
    """
    try:
        url = f"{ZOHO_CRM_BASE_URL}/settings/users"
        params = {"type": user_type}
        response = make_authenticated_request("GET", url, params=params)

        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get("users", [])
            return {
                "status": "success",
                "user_type": user_type,
                "count": len(users),
                "users": users
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to fetch users: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error fetching users: {str(e)}"
        }


@mcp.tool()
def qualify_lead(ctx, lead_id: str, qualification_data: Any):
    """
    Update lead qualification status and convert to contact/deal if qualified

    Args:
        lead_id: ID of the lead to qualify
        qualification_data: Dictionary or JSON string containing qualification information
                           Example: {
                               "Lead_Status": "Qualified",
                               "Rating": "Hot",
                               "Annual_Revenue": "100000",
                               "No_of_Employees": "25"
                           }
    """
    
    # Handle both string and dict
    if isinstance(qualification_data, str):
        try:
            data_dict = json.loads(qualification_data)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in qualification_data: {str(e)}"
            }
    elif isinstance(qualification_data, dict):
        data_dict = qualification_data
    else:
        return {
            "status": "error",
            "message": f"Invalid qualification_data type: {type(qualification_data)}"
        }
    
    # Validate not empty
    if not data_dict:
        return {
            "status": "error",
            "message": "qualification_data is empty! Cannot qualify with no fields."
        }
    
    try:
        # Update lead with qualification data
        url = f"{ZOHO_CRM_BASE_URL}/Leads/{lead_id}"
        payload = {"data": [data_dict]}

        response = make_authenticated_request("PUT", url, json=payload)

        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "message": "Lead qualified successfully",
                "lead_id": lead_id,
                "data": result.get("data", [])
            }
        else:
            return {
                "status": "error",
                "lead_id": lead_id,
                "message": f"Failed to qualify lead: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "lead_id": lead_id,
            "message": f"Error qualifying lead: {str(e)}"
        }

@mcp.tool()
def convert_lead(ctx, lead_id: str, conversion_data: Any = None):
    """
    Convert a qualified lead to Contact, Account, and Deal

    Args:
        lead_id: ID of the lead to convert
        conversion_data: Optional dictionary or JSON string with conversion settings
                        Example: {
                            "notify_lead_owner": True,
                            "notify_new_entity_owner": True,
                            "accounts": "Account_Name",
                            "deals": "Deal_Name"
                        }
    """
    
    # Handle both string and dict
    if conversion_data:
        if isinstance(conversion_data, str):
            try:
                data_dict = json.loads(conversion_data)
            except json.JSONDecodeError as e:
                return {
                    "status": "error",
                    "message": f"Invalid JSON in conversion_data: {str(e)}"
                }
        elif isinstance(conversion_data, dict):
            data_dict = conversion_data
        else:
            return {
                "status": "error",
                "message": f"Invalid conversion_data type: {type(conversion_data)}"
            }
    else:
        # Default conversion data
        data_dict = {
            "notify_lead_owner": True,
            "notify_new_entity_owner": True
        }
    
    try:
        url = f"{ZOHO_CRM_BASE_URL}/Leads/{lead_id}/actions/convert"
        payload = {"data": [data_dict]}
        
        response = make_authenticated_request("POST", url, json=payload)

        if response.status_code == 200:
            result = response.json()
            return {
                "status": "success",
                "message": "Lead converted successfully",
                "lead_id": lead_id,
                "data": result.get("data", [])
            }
        else:
            return {
                "status": "error",
                "lead_id": lead_id,
                "message": f"Failed to convert lead: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "lead_id": lead_id,
            "message": f"Error converting lead: {str(e)}"
        }

@mcp.tool()
def create_task(ctx, task_data: Any, related_module: str = "Leads"):
    """
    Create a task in Zoho CRM for follow-up activities

    Args:
        task_data: Dictionary or JSON string containing task details
                  Example: {
                      "Subject": "Follow up with lead",
                      "What_Id": "lead_id_here",
                      "Due_Date": "2024-01-20",
                      "Status": "Not Started",
                      "Priority": "High"
                  }
        related_module: The module the task is related to (default: "Leads")
                       Options: "Leads", "Contacts", "Deals", "Accounts"
    """
    
    # Handle both string and dict
    if isinstance(task_data, str):
        try:
            data_dict = json.loads(task_data)
        except json.JSONDecodeError as e:
            return {
                "status": "error",
                "message": f"Invalid JSON in task_data: {str(e)}"
            }
    elif isinstance(task_data, dict):
        data_dict = task_data
    else:
        return {
            "status": "error",
            "message": f"Invalid task_data type: {type(task_data)}"
        }
    
    # Validate not empty
    if not data_dict:
        return {
            "status": "error",
            "message": "task_data is empty! Cannot create task with no fields."
        }
    
    # CRITICAL: Add $se_module field if What_Id is present
    # This tells Zoho which module the related record belongs to
    if "What_Id" in data_dict and "$se_module" not in data_dict:
        data_dict["$se_module"] = related_module
    
    try:
        url = f"{ZOHO_CRM_BASE_URL}/Tasks"
        payload = {"data": [data_dict]}
        response = make_authenticated_request("POST", url, json=payload)

        if response.status_code == 201:
            result = response.json()
            return {
                "status": "success",
                "message": "Task created successfully",
                "data": result.get("data", [])
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to create task: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating task: {str(e)}"
        }

@mcp.tool()
def get_module_fields(ctx, module_name: str):
    """Get all fields and their API names for a module"""
    url = f"{ZOHO_CRM_BASE_URL}/settings/fields"
    params = {"module": module_name}
    
    response = make_authenticated_request("GET", url, params=params)
    
    if response.status_code == 200:
        fields_data = response.json()
        fields = fields_data.get("fields", [])
        
        # Filter to show only name-related fields
        field_info = []
        for field in fields:
            api_name = field.get("api_name", "")
            if "name" in api_name.lower() or field.get("required"):
                field_info.append({
                    "field_label": field.get("field_label"),
                    "api_name": api_name,
                    "data_type": field.get("data_type"),
                    "required": field.get("required", False)
                })
        
        return {
            "status": "success",
            "module": module_name,
            "total_fields": len(fields),
            "name_and_required_fields": field_info
        }
    else:
        return {
            "status": "error",
            "message": response.text,
            "code": response.status_code
        }
    
@mcp.tool()
def debug_create_lead(ctx, first_name: str, last_name: str, company: str = "Unknown"):
    """
    Debug version of create_record that logs everything
    """
    if not ensure_valid_token():
        return {"error": "No tokens"}
    
    # Build the exact same payload as create_record
    record_data = {
        "First_Name": first_name,
        "Last_Name": last_name,
        "Company": company
    }
    
    payload = {"data": [record_data]}
    
    # Log what we're sending
    import json
    payload_str = json.dumps(payload, indent=2)
    
    url = f"{ZOHO_CRM_BASE_URL}/Leads"
    response = make_authenticated_request("POST", url, json=payload)
    
    return {
        "url_sent_to": url,
        "payload_sent": payload_str,
        "status_code": response.status_code,
        "response_text": response.text
    }    

@mcp.tool()
def get_lead_activities(ctx, lead_id: str):
    """
    Get all activities (tasks, events, calls) for a specific lead

    Args:
        lead_id: ID of the lead to get activities for
    """
    try:
        activities = {}

        # Get tasks
        tasks_url = f"{ZOHO_CRM_BASE_URL}/Leads/{lead_id}/Tasks"
        tasks_response = make_authenticated_request("GET", tasks_url)
        if tasks_response.status_code == 200:
            activities["tasks"] = tasks_response.json().get("data", [])

        # Get events
        events_url = f"{ZOHO_CRM_BASE_URL}/Leads/{lead_id}/Events"
        events_response = make_authenticated_request("GET", events_url)
        if events_response.status_code == 200:
            activities["events"] = events_response.json().get("data", [])

        # Get calls
        calls_url = f"{ZOHO_CRM_BASE_URL}/Leads/{lead_id}/Calls"
        calls_response = make_authenticated_request("GET", calls_url)
        if calls_response.status_code == 200:
            activities["calls"] = calls_response.json().get("data", [])

        return {
            "status": "success",
            "lead_id": lead_id,
            "activities": activities
        }

    except Exception as e:
        return {
            "status": "error",
            "lead_id": lead_id,
            "message": f"Error fetching activities: {str(e)}"
        }
    

def get_calendar_auth_headers():
    """Get authorization headers for Calendar API"""
    # Use the same access token as CRM (they share the same token with proper scopes)
    if not current_access_token:
        ensure_valid_token()
    
    return {
        "Authorization": f"Zoho-oauthtoken {current_access_token}",
        "Content-Type": "application/json"
    }
    
@mcp.tool()
def check_calendar_availability(ctx=None, date: str = None, start_time: str = None, 
                                 end_time: str = None, exclude_meeting_id: str = None):
    """
    Check if calendar is available during a specific time using CRM Events
    
    Args:
        date: Date in YYYY-MM-DD format (e.g., '2025-10-25')
        start_time: Start time in HH:MM format (e.g., '14:00')
        end_time: End time in HH:MM format (e.g., '16:00')
        exclude_meeting_id: Meeting ID to exclude from conflict check (for updates)
    """
    
    if not date or not start_time or not end_time:
        return {"status": "error", "message": "Missing required parameters"}
    
    try:
        from datetime import datetime
        
        url = f"{ZOHO_CRM_BASE_URL}/Events"
        
        params = {
            "fields": "id,Event_Title,Start_DateTime,End_DateTime",
            "per_page": 200
        }
        
        headers = get_auth_headers()
        response = make_authenticated_request("GET", url, params=params)
        
        if response.status_code == 204:
            return {
                "status": "free",
                "available": True,
                "message": f"Available from {start_time} to {end_time} on {date}"
            }
        elif response.status_code == 200:
            all_events = response.json().get("data", [])
            
            request_start = datetime.fromisoformat(f"{date}T{start_time}:00")
            request_end = datetime.fromisoformat(f"{date}T{end_time}:00")
            request_date = datetime.fromisoformat(date).date()
            
            conflicts = []
            for event in all_events:
                # Skip the meeting we're updating
                if exclude_meeting_id and event.get("id") == exclude_meeting_id:
                    continue
                
                event_start_str = event.get("Start_DateTime", "")
                event_end_str = event.get("End_DateTime", "")
                
                if event_start_str and event_end_str:
                    try:
                        event_start = datetime.fromisoformat(
                            event_start_str.split('+')[0].split('-05:')[0].split('Z')[0]
                        )
                        event_end = datetime.fromisoformat(
                            event_end_str.split('+')[0].split('-05:')[0].split('Z')[0]
                        )
                        
                        if event_start.date() != request_date:
                            continue
                        
                        if not (request_end <= event_start or request_start >= event_end):
                            conflicts.append({
                                "title": event.get("Event_Title"),
                                "start": event_start_str,
                                "end": event_end_str
                            })
                    except Exception as e:
                        continue
            
            if conflicts:
                return {
                    "status": "busy",
                    "available": False,
                    "conflicts": conflicts,
                    "message": f"Not available. {len(conflicts)} conflicting event(s) found."
                }
            else:
                return {
                    "status": "free",
                    "available": True,
                    "message": f"Available from {start_time} to {end_time} on {date}",
                    "total_events_checked": len(all_events)
                }
        else:
            return {
                "status": "error",
                "message": response.text,
                "code": response.status_code
            }
    except Exception as e:
        return {"status": "error", "message": f"Error checking availability: {str(e)}"}
    
@mcp.tool()
def book_meeting(attendee_email: str = None, date: str = None, start_time: str = None, 
                 end_time: str = None, title: str = None, description: str = "", 
                 meeting_link: str = "", lead_id = None):
    """
    Book a meeting with auto-generated Zoho Meeting link and calendar invite
    
    Args:
        attendee_email: Email address of the person to meet with
        date: Date in YYYY-MM-DD format (e.g., '2025-10-25')
        start_time: Start time in HH:MM format (e.g., '14:00')
        end_time: End time in HH:MM format (e.g., '16:00')
        title: Meeting title/subject
        description: Meeting description/agenda
        meeting_link: Optional - Custom Zoom/Google Meet link (if not provided, auto-generates Zoho Meeting)
        lead_id: Optional - Link event to a specific lead/contact
    """
    
    if not all([attendee_email, date, start_time, end_time, title]):
        return {
            "status": "error",
            "message": "Missing required parameters"
        }
    
    try:
        # Step 1: Check availability
        availability = check_calendar_availability(None, date, start_time, end_time)
        
        if availability.get("status") == "busy":
            return {
                "status": "unavailable",
                "message": f"Time slot not available",
                "conflicts": availability.get("conflicts")
            }
        
        # Prepare datetime strings
        start_datetime = f"{date}T{start_time}:00"
        end_datetime = f"{date}T{end_time}:00"
        
        # Step 2: Create calendar event with invite (will auto-generate Zoho Meeting link)
        calendar_response = create_calendar_event_with_invite(
            title=title,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            attendee_email=attendee_email,
            description=description,
            location=meeting_link if meeting_link else ""
        )
        
        # Get auto-generated meeting link from calendar response
        auto_meeting_link = calendar_response.get("meeting_link")
        
        # Use auto-generated link if no custom link was provided
        final_meeting_link = meeting_link if meeting_link else auto_meeting_link
        
        # Build full description with meeting link
        full_description = description
        if final_meeting_link:
            full_description = f"{description}\n\nJoin Meeting: {final_meeting_link}" if description else f"Join Meeting: {final_meeting_link}"
        
        # Step 3: Create event in CRM (for tracking and workflow trigger)
        url = f"{ZOHO_CRM_BASE_URL}/Events"
        
        event_data = {
            "Event_Title": title,
            "Start_DateTime": start_datetime,
            "End_DateTime": end_datetime,
            "Description": full_description,
            "Location": final_meeting_link if final_meeting_link else "",
            "Tag": ["AI_Booking"],
            "Participants": [{"participant": attendee_email, "type": "email"}]
        }
        
        if lead_id:
            event_data["What_Id"] = lead_id
            event_data["$se_module"] = "Leads"
        
        payload = {"data": [event_data]}
        crm_response = make_authenticated_request("POST", url, json=payload)
        
        if crm_response.status_code != 201:
            return {
                "status": "error",
                "message": f"Failed to create CRM event: {crm_response.text}",
                "code": crm_response.status_code
            }
        
        crm_result = crm_response.json()
        
        # Return combined result
        return {
            "status": "success",
            "message": f"Meeting booked successfully! Zoho Meeting link auto-generated and calendar invite sent to {attendee_email}",
            "meeting_details": {
                "title": title,
                "date": date,
                "start_time": start_time,
                "end_time": end_time,
                "attendee": attendee_email,
                "description": description,
                "meeting_link": final_meeting_link,
                "link_type": "custom" if meeting_link else "auto-generated Zoho Meeting"
            },
            "crm_event": crm_result.get("data", []),
            "calendar_invite": calendar_response
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error booking meeting: {str(e)}"
        }
    
@mcp.tool()
def create_calendar_event_with_invite(title: str = None, start_datetime: str = None, 
                                       end_datetime: str = None, attendee_email: str = None,
                                       description: str = "", location: str = ""):
    """
    Create event in Zoho Calendar with calendar invite and auto-generated Zoho Meeting link
    
    Args:
        title: Event title
        start_datetime: Start in ISO format (e.g., '2025-11-05T10:00:00')
        end_datetime: End in ISO format (e.g., '2025-11-05T11:00:00')
        attendee_email: Email to send calendar invite to
        description: Event description/agenda
        location: Meeting location or link
    """
    
    if not all([title, start_datetime, end_datetime, attendee_email]):
        return {
            "status": "error",
            "message": "Missing required parameters"
        }
    
    try:
        import json
        
        # AI Agent's calendar UID
        calendar_uid = "ef74750c5e154a6f8bb9a7bdf6249d83"
        
        # Datetime format
        start_formatted = start_datetime.replace('-', '').replace(':', '')
        end_formatted = end_datetime.replace('-', '').replace(':', '')
        
        # Build event data according to Zoho format
        event_data = {
            "title": title,
            "dateandtime": {
                "start": start_formatted,
                "end": end_formatted,
                "timezone": "America/New_York"
            },
            "description": description,
            "location": location,
            "attendees": [
                {
                    "email": attendee_email,
                    "permission": 1  # View permission
                }
            ],
            "conference": "zmeeting",  # ← ADD THIS LINE! Auto-generates Zoho Meeting link
            "reminders": [
                {
                    "action": "popup",
                    "minutes": -15  # 15 mins before (negative value)
                }
            ],
            "isallday": False,
            "isprivate": False,
            "transparency": 0,  # Add to free/busy
            "calendar_alarm": True
        }
        
        # Convert to JSON string for query parameter
        eventdata_json = json.dumps(event_data)
        
        # Create URL with eventdata as query parameter
        url = f"https://calendar.zoho.com/api/v1/calendars/{calendar_uid}/events"
        
        # Pass eventdata as query parameter
        params = {
            "eventdata": eventdata_json
        }
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {current_access_token}"
        }
        
        # POST request with eventdata in query params
        response = requests.post(url, headers=headers, params=params)
        
        if response.status_code in [200, 201]:
            result = response.json()
            
            # Extract the auto-generated meeting link from response
            events = result.get("events", [])
            meeting_link = None
            
            if events:
                event = events[0]
                # Check for meeting link in conference_data or app_data
                conference_data = event.get("conference_data", {})
                app_data = event.get("app_data", {})
                
                if conference_data:
                    meeting_data = conference_data.get("meetingdata", {})
                    meeting_link = meeting_data.get("meeting_link") or meeting_data.get("meetinglink")
                elif app_data:
                    meeting_data = app_data.get("meetingdata", {})
                    meeting_link = meeting_data.get("meeting_link") or meeting_data.get("meetinglink")
            
            return {
                "status": "success",
                "message": f"Calendar event created with Zoho Meeting link and invite sent to {attendee_email}",
                "meeting_link": meeting_link,  # Include the auto-generated link
                "event_data": result
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to create calendar event: {response.text}",
                "code": response.status_code
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error creating calendar event: {str(e)}"
        }
    
def find_calendar_event_by_crm_id(crm_event_id: str):
    """
    Find Zoho Calendar event that corresponds to a CRM event
    """
    try:
        # Get CRM event details
        crm_url = f"{ZOHO_CRM_BASE_URL}/Events/{crm_event_id}"
        crm_response = make_authenticated_request("GET", crm_url)
        
        if crm_response.status_code != 200:
            print(f"Failed to get CRM event: {crm_response.status_code}")
            return None
        
        crm_event = crm_response.json().get("data", [])[0]
        event_title = crm_event.get("Event_Title")
        start_datetime = crm_event.get("Start_DateTime", "")
        
        print(f"Looking for calendar event with title: '{event_title}'")
        
        # Extract date
        event_date = start_datetime.split("T")[0] if "T" in start_datetime else None
        
        if not event_date:
            print("No date found in CRM event")
            return None
        
        print(f"Event date: {event_date}")
        
        # Search Zoho Calendar
        calendar_uid = "ef74750c5e154a6f8bb9a7bdf6249d83"
        date_formatted = event_date.replace("-", "")
        
        cal_url = f"https://calendar.zoho.com/api/v1/calendars/{calendar_uid}/events"
        
        params = {
            "range": "custom",
            "sdate": date_formatted,
            "edate": date_formatted
        }
        
        headers = {
            "Authorization": f"Zoho-oauthtoken {current_access_token}"
        }
        
        cal_response = requests.get(cal_url, headers=headers, params=params)
        
        print(f"Calendar API response status: {cal_response.status_code}")
        
        if cal_response.status_code == 200:
            calendar_events = cal_response.json().get("events", [])
            print(f"Found {len(calendar_events)} events on {event_date}")
            
            # Find matching event by title
            for cal_event in calendar_events:
                cal_title = cal_event.get("title", "")
                print(f"Comparing: CRM='{event_title}' vs Calendar='{cal_title}'")
                if cal_title == event_title:
                    uid = cal_event.get("uid")
                    print(f"Match found! Calendar UID: {uid}")
                    return uid
            
            print("No matching title found in calendar events")
        else:
            print(f"Calendar API error: {cal_response.text}")
        
        return None
        
    except Exception as e:
        print(f"Error finding calendar event: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
@mcp.tool()
def update_meeting(meeting_id: str = None, new_date = None, new_start_time = None,
                   new_end_time = None, new_title = None, new_description = None,
                   new_meeting_link = None):
    """
    Update an existing meeting's details in both CRM and Calendar
    """
    
    if not meeting_id:
        return {"status": "error", "message": "Meeting ID is required"}
    
    try:
        import json
        
        # Get current meeting details first (for attendee email)
        crm_url = f"{ZOHO_CRM_BASE_URL}/Events/{meeting_id}"
        current_meeting_response = make_authenticated_request("GET", crm_url)
        
        if current_meeting_response.status_code != 200:
            return {"status": "error", "message": "Could not fetch current meeting details"}
        
        current_meeting = current_meeting_response.json().get("data", [])[0]
        current_title = current_meeting.get("Event_Title")
        current_description = current_meeting.get("Description", "")
        current_location = current_meeting.get("Location", "")
        
        # Get attendee email
        participants = current_meeting.get("Participants", [])
        attendee_email = participants[0].get("participant") if participants else None
        
        # Build CRM update data
        crm_update_data = {}
        
        if new_date and new_start_time and new_end_time:
            availability = check_calendar_availability(
                None, new_date, new_start_time, new_end_time, 
                exclude_meeting_id=meeting_id
            )
            
            if availability.get("status") == "busy":
                return {
                    "status": "unavailable",
                    "message": f"New time slot not available",
                    "conflicts": availability.get("conflicts")
                }
            
            crm_update_data["Start_DateTime"] = f"{new_date}T{new_start_time}:00"
            crm_update_data["End_DateTime"] = f"{new_date}T{new_end_time}:00"
        
        if new_title:
            crm_update_data["Event_Title"] = new_title
        
        if new_description or new_meeting_link:
            desc = new_description if new_description else current_description
            if new_meeting_link:
                desc = f"{desc}\n\nJoin Meeting: {new_meeting_link}" if desc else f"Join Meeting: {new_meeting_link}"
            crm_update_data["Description"] = desc
        
        if new_meeting_link:
            crm_update_data["Location"] = new_meeting_link
        
        if not crm_update_data:
            return {"status": "error", "message": "No fields to update"}
        
        # Update CRM Event
        update_url = f"{ZOHO_CRM_BASE_URL}/Events/{meeting_id}"
        crm_payload = {"data": [crm_update_data]}
        
        crm_response = make_authenticated_request("PUT", update_url, json=crm_payload)
        
        if crm_response.status_code != 200:
            return {
                "status": "error",
                "message": f"Failed to update CRM: {crm_response.text}",
                "code": crm_response.status_code
            }
        
        crm_result = crm_response.json()
        
        # Recreate calendar event with new time (if datetime changed and we have attendee)
        calendar_result = None
        if new_date and new_start_time and new_end_time and attendee_email:
            # Use final values (new or current)
            final_title = new_title if new_title else current_title
            final_description = crm_update_data.get("Description", current_description)
            final_location = new_meeting_link if new_meeting_link else current_location
            final_start = f"{new_date}T{new_start_time}:00"
            final_end = f"{new_date}T{new_end_time}:00"
            
            # Create new calendar event with updated time
            calendar_result = create_calendar_event_with_invite(
                title=final_title,
                start_datetime=final_start,
                end_datetime=final_end,
                attendee_email=attendee_email,
                description=final_description,
                location=final_location
            )
        
        return {
            "status": "success",
            "message": "Meeting updated successfully. New calendar invite sent.",
            "crm_update": crm_result.get("data", []),
            "calendar_update": calendar_result
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error updating meeting: {str(e)}"
        }
    
@mcp.tool()
def find_meeting(title: str = None, date = None, attendee_email = None):
    """
    Find a meeting by title, date, or attendee email
    
    Args:
        title: Meeting title (exact match or partial)
        date: Meeting date in YYYY-MM-DD format
        attendee_email: Attendee's email address
    
    Returns meeting ID and details
    """
    
    if not any([title, date, attendee_email]):
        return {
            "status": "error",
            "message": "Provide at least one search criteria (title, date, or attendee_email)"
        }
    
    try:
        # If only title is provided, get all events and filter in code
        if title and not date:
            url = f"{ZOHO_CRM_BASE_URL}/Events"
            params = {
                "fields": "id,Event_Title,Start_DateTime,End_DateTime,Description,Location,Participants",
                "per_page": 200
            }
            
            response = make_authenticated_request("GET", url, params=params)
            
            if response.status_code == 200:
                all_meetings = response.json().get("data", [])
                
                # Filter by title (case-insensitive partial match)
                title_lower = title.lower()
                meetings = [m for m in all_meetings if title_lower in m.get("Event_Title", "").lower()]
                
                # Filter by attendee if provided
                if attendee_email:
                    meetings = [m for m in meetings if attendee_email in str(m.get("Participants", []))]
                
                if meetings:
                    return {
                        "status": "success",
                        "count": len(meetings),
                        "meetings": meetings
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": f"No meetings found with title containing '{title}'"
                    }
            elif response.status_code == 204:
                return {
                    "status": "not_found",
                    "message": "No meetings found"
                }
        
        # If date is provided, use search with date criteria
        elif date:
            url = f"{ZOHO_CRM_BASE_URL}/Events/search"
            
            criteria = f"(Start_DateTime:starts_with:{date})"
            
            params = {
                "criteria": criteria,
                "fields": "id,Event_Title,Start_DateTime,End_DateTime,Description,Location,Participants"
            }
            
            response = make_authenticated_request("GET", url, params=params)
            
            if response.status_code == 200:
                meetings = response.json().get("data", [])
                
                # Filter by title if provided
                if title:
                    title_lower = title.lower()
                    meetings = [m for m in meetings if title_lower in m.get("Event_Title", "").lower()]
                
                # Filter by attendee if provided
                if attendee_email:
                    meetings = [m for m in meetings if attendee_email in str(m.get("Participants", []))]
                
                if meetings:
                    return {
                        "status": "success",
                        "count": len(meetings),
                        "meetings": meetings
                    }
                else:
                    return {
                        "status": "not_found",
                        "message": "No meetings found matching criteria"
                    }
            elif response.status_code == 204:
                return {
                    "status": "not_found",
                    "message": "No meetings found on that date"
                }
        
        return {
            "status": "error",
            "message": response.text,
            "code": response.status_code
        }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error finding meeting: {str(e)}"
        }
    
@mcp.tool()
def create_note(ctx, parent_id: str, note_title: str, note_content: str, parent_module: str = "Leads"):
    """
    Create a note attached to a lead, contact, deal, or account

    Args:
        parent_id: ID of the record to attach the note to
        note_title: Title of the note
        note_content: Content/body of the note
        parent_module: Module of the parent record (default: "Leads")
                      Options: "Leads", "Contacts", "Deals", "Accounts"
    """
    
    url = f"{ZOHO_CRM_BASE_URL}/Notes"
    
    note_data = {
        "Note_Title": note_title,
        "Note_Content": note_content,
        "Parent_Id": {
            "id": parent_id
        },
        "$se_module": parent_module
    }
    
    payload = {"data": [note_data]}
    
    response = make_authenticated_request("POST", url, json=payload)
    
    if response.status_code == 201:
        result = response.json()
        return {
            "status": "success",
            "message": "Note created successfully",
            "parent_id": parent_id,
            "parent_module": parent_module,
            "data": result.get("data", [])
        }
    else:
        return {
            "status": "error",
            "message": f"Failed to create note: {response.status_code} - {response.text}"
        }
    
@mcp.tool()
def get_notes(ctx, parent_id: str):
    """
    Get all notes attached to a specific record (lead, contact, deal, account)

    Args:
        parent_id: ID of the record to get notes for
    """
    
    url = f"{ZOHO_CRM_BASE_URL}/Notes/search"
    params = {
        "criteria": f"(Parent_Id:equals:{parent_id})",
        "fields": "id,Note_Title,Note_Content,Owner,Created_Time,Modified_Time"
    }
    
    response = make_authenticated_request("GET", url, params=params)
    
    if response.status_code == 204:
        return {
            "status": "success",
            "count": 0,
            "message": "No notes found for this record",
            "data": []
        }
    elif response.status_code == 200:
        data = response.json().get("data", [])
        return {
            "status": "success",
            "count": len(data),
            "parent_id": parent_id,
            "data": data
        }
    else:
        return {
            "status": "error",
            "message": response.text,
            "code": response.status_code
        }

def main():
    """Main entry point for the MCP server"""
    global current_access_token, current_refresh_token

    # Validate required environment variables
    if not ZOHO_CLIENT_ID or not ZOHO_CLIENT_SECRET:
        print("ERROR: Missing required Zoho credentials.")
        print("Please ensure ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET are set in .env.local")
        return

    print(f"Starting Zoho CRM MCP Server...")
    print(f"Client ID: {ZOHO_CLIENT_ID[:10]}..." if ZOHO_CLIENT_ID else "Client ID: Not set")
    print(f"API Base URL: {ZOHO_CRM_BASE_URL}")

    # Initialize tokens
    print("Initializing OAuth tokens...")
    if ensure_valid_token():
        print("SUCCESS: OAuth tokens ready - server is autonomous!")
    else:
        print("WARNING: No valid tokens found.")
        print("   The server will start, but you'll need to:")
        print("   1. Use the 'set_refresh_token' tool to provide a long-lived refresh token")
        print("   2. Or complete OAuth setup manually and update .env.local")
        print("   3. Use 'test_zoho_connection' to verify connectivity")

    mcp.run()

if __name__ == "__main__":
    main()