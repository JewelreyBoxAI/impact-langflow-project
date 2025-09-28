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
def get_module_data(ctx, module_name: str = None):
    """
    Fetch data from Zoho CRM modules

    Args:
        module_name: Specific module name (e.g., 'Contacts', 'Leads').
                    If None, fetches from all modules.
    """

    if module_name:
        url = f"{ZOHO_CRM_BASE_URL}/{module_name}"
        response = make_authenticated_request("GET", url)
        
        if response.status_code == 200:
            data = response.json().get("data", [])
            return {
                "status": "success",
                "module": module_name,
                "count": len(data),
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
        all_data = {}
        errors = []
        
        for module in ZOHO_MODULES:
            url = f"{ZOHO_CRM_BASE_URL}/{module}"
            response = make_authenticated_request("GET", url)
            
            if response.status_code == 200:
                data = response.json().get("data", [])
                all_data[module] = {
                    "count": len(data),
                    "data": data
                }
            else:
                errors.append({
                    "module": module,
                    "code": response.status_code,
                    "message": response.text
                })
        
        return {
            "status": "success",
            "modules_fetched": len(all_data),
            "total_records": sum(module_data["count"] for module_data in all_data.values()),
            "data": all_data,
            "errors": errors if errors else None
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
        search_criteria: Search query (e.g., 'email:john@example.com')
    """

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}/search"
    params = {"criteria": search_criteria}

    response = make_authenticated_request("GET", url, params=params)
    
    if response.status_code == 200:
        data = response.json().get("data", [])
        return {
            "status": "success",
            "module": module_name,
            "count": len(data),
            "data": data
        }
    else:
        return {
            "status": "error",
            "module": module_name,
            "message": response.text,
            "code": response.status_code
        }

@mcp.tool()
def create_record(ctx, module_name: str, record_data: dict):
    """
    Create a new record in a specific module

    Args:
        module_name: Module to create record in (e.g., 'Contacts', 'Leads')
        record_data: Dictionary containing the record fields and values
                    Example: {"First_Name": "John", "Last_Name": "Doe", "Email": "john@example.com"}
    """

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}"

    # Wrap the record data in the required format
    payload = {
        "data": [record_data]
    }

    response = make_authenticated_request("POST", url, data=json.dumps(payload))
    
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
def update_record(ctx, module_name: str, record_id: str, record_data: dict):
    """
    Update an existing record in a specific module

    Args:
        module_name: Module containing the record (e.g., 'Contacts', 'Leads')
        record_id: ID of the record to update
        record_data: Dictionary containing the fields to update and their new values
                    Example: {"First_Name": "Jane", "Email": "jane@example.com"}
    """

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}/{record_id}"

    # Add the record ID to the data
    record_data["id"] = record_id

    # Wrap the record data in the required format
    payload = {
        "data": [record_data]
    }

    response = make_authenticated_request("PUT", url, data=json.dumps(payload))
    
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
def bulk_create_records(ctx, module_name: str, records_data: list):
    """
    Create multiple records in a specific module

    Args:
        module_name: Module to create records in (e.g., 'Contacts', 'Leads')
        records_data: List of dictionaries containing record data
                     Example: [{"First_Name": "John", "Last_Name": "Doe"}, {"First_Name": "Jane", "Last_Name": "Smith"}]
    """

    url = f"{ZOHO_CRM_BASE_URL}/{module_name}"

    # Zoho CRM allows up to 100 records per API call
    if len(records_data) > 100:
        return {
            "status": "error",
            "message": "Maximum 100 records allowed per bulk operation"
        }

    payload = {
        "data": records_data
    }

    response = make_authenticated_request("POST", url, data=json.dumps(payload))
    
    if response.status_code == 201:
        result = response.json()
        return {
            "status": "success",
            "module": module_name,
            "message": f"{len(records_data)} records created successfully",
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

        # Try to get user info (lightweight API call)
        url = f"{ZOHO_CRM_BASE_URL}/settings/users"
        response = make_authenticated_request("GET", url, params={"type": "current_user"})

        if response.status_code == 200:
            user_data = response.json()
            return {
                "status": "success",
                "message": "Successfully connected to Zoho CRM",
                "user_info": user_data.get("users", [{}])[0] if user_data.get("users") else {},
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
def schedule_appointment(ctx, lead_id: str, appointment_data: dict):
    """
    Schedule an appointment/event for a lead in Zoho CRM

    Args:
        lead_id: ID of the lead to schedule appointment for
        appointment_data: Dictionary containing appointment details
                         Example: {
                             "Event_Title": "Initial Consultation",
                             "Start_DateTime": "2024-01-15T10:00:00-05:00",
                             "End_DateTime": "2024-01-15T11:00:00-05:00",
                             "Description": "Meet with potential client"
                         }
    """
    try:
        # Add the lead as a participant
        appointment_data["What_Id"] = lead_id
        appointment_data["Participants"] = [{
            "type": "lead",
            "participant": lead_id
        }]

        # Create event
        url = f"{ZOHO_CRM_BASE_URL}/Events"
        payload = {"data": [appointment_data]}
        response = make_authenticated_request("POST", url, data=json.dumps(payload))

        if response.status_code == 201:
            result = response.json()
            return {
                "status": "success",
                "message": "Appointment scheduled successfully",
                "data": result.get("data", [])
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to schedule appointment: {response.status_code} - {response.text}"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error scheduling appointment: {str(e)}"
        }

@mcp.tool()
def qualify_lead(ctx, lead_id: str, qualification_data: dict):
    """
    Update lead qualification status and convert to contact/deal if qualified

    Args:
        lead_id: ID of the lead to qualify
        qualification_data: Dictionary containing qualification information
                           Example: {
                               "Lead_Status": "Qualified",
                               "Rating": "Hot",
                               "Annual_Revenue": "100000",
                               "No_of_Employees": "25"
                           }
    """
    try:
        # Update lead with qualification data
        url = f"{ZOHO_CRM_BASE_URL}/Leads/{lead_id}"
        qualification_data["id"] = lead_id
        payload = {"data": [qualification_data]}

        response = make_authenticated_request("PUT", url, data=json.dumps(payload))

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
def convert_lead(ctx, lead_id: str, conversion_data: dict = None):
    """
    Convert a qualified lead to Contact, Account, and Deal

    Args:
        lead_id: ID of the lead to convert
        conversion_data: Optional dictionary with conversion settings
                        Example: {
                            "notify_lead_owner": True,
                            "notify_new_entity_owner": True,
                            "accounts": "Account_Name",
                            "deals": "Deal_Name"
                        }
    """
    try:
        url = f"{ZOHO_CRM_BASE_URL}/Leads/{lead_id}/actions/convert"

        # Default conversion data
        if not conversion_data:
            conversion_data = {
                "notify_lead_owner": True,
                "notify_new_entity_owner": True
            }

        payload = {"data": [conversion_data]}
        response = make_authenticated_request("POST", url, data=json.dumps(payload))

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
def create_task(ctx, task_data: dict):
    """
    Create a task in Zoho CRM for follow-up activities

    Args:
        task_data: Dictionary containing task details
                  Example: {
                      "Subject": "Follow up with lead",
                      "What_Id": "lead_id_here",
                      "Due_Date": "2024-01-20",
                      "Status": "Not Started",
                      "Priority": "High"
                  }
    """
    try:
        url = f"{ZOHO_CRM_BASE_URL}/Tasks"
        payload = {"data": [task_data]}
        response = make_authenticated_request("POST", url, data=json.dumps(payload))

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