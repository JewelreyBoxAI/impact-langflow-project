import httpx
import time
import os
import json
from pathlib import Path

# Token persistence file
TOKEN_FILE = Path(__file__).parent / "salesmsg_tokens.json"

# Get credentials from environment variables
SALESMSG_CLIENT_ID = os.getenv("SALESMSG_CLIENT_ID")
SALESMSG_CLIENT_SECRET = os.getenv("SALESMSG_CLIENT_SECRET")
SALESMSG_REFRESH_TOKEN = os.getenv("SALESMSG_REFRESH_TOKEN")
SALESMSG_BASE_URL = os.getenv("SALESMSG_BASE_URL", "https://api.salesmessage.com/pub/v2.2")
SALESMSG_TEAM_ID = os.getenv("SALESMSG_TEAM_ID", "186244")

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
                print(f"[DEBUG] Tokens loaded from cache")
                return True
    except Exception as e:
        print(f"[WARN] Failed to load tokens: {e}")

    # Fallback to environment variables
    if SALESMSG_REFRESH_TOKEN:
        current_refresh_token = SALESMSG_REFRESH_TOKEN
        print(f"[DEBUG] Using refresh token from environment")

    return current_refresh_token is not None

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
        "expires_in": expires_in or 86340
    }

    try:
        # Ensure parent directory exists
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        print("[INFO] Salesmsg tokens saved successfully")
    except Exception as e:
        print(f"[ERROR] Failed to save tokens: {e}")

def refresh_access_token():
    """Refresh the Salesmsg access token using refresh token"""
    global current_access_token, current_refresh_token

    if not current_refresh_token:
        return {"error": "No refresh token available. Need to complete OAuth setup first."}

    data = {
        "grant_type": "refresh_token",
        "client_id": SALESMSG_CLIENT_ID,
        "client_secret": SALESMSG_CLIENT_SECRET,
        "refresh_token": current_refresh_token
    }

    try:
        response = httpx.post(f"{SALESMSG_BASE_URL}/oauth/token", data=data)
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")  # Salesmsg rotates refresh tokens
            
            # CRITICAL: Save the NEW refresh token if provided
            if new_refresh_token:
                print("[INFO] ⚠️ New refresh token received - updating .env recommended!")
                print(f"SALESMSG_REFRESH_TOKEN={new_refresh_token}")
            
            save_tokens(
                access_token=new_access_token, 
                refresh_token=new_refresh_token or current_refresh_token,
                expires_in=token_data.get("expires_in")
            )
            
            return {"success": True, "token": new_access_token}
        else:
            return {"error": f"Token refresh failed: {response.text}"}
    except Exception as e:
        return {"error": f"Token refresh error: {str(e)}"}

def ensure_valid_token():
    """Ensure we have a valid access token, generate if needed"""
    global current_access_token, current_refresh_token

    # Try to load existing tokens first
    if not current_access_token:
        load_tokens()

    # If we have a refresh token but no access token, try to refresh
    if current_refresh_token and not current_access_token:
        print("[INFO] No access token found, refreshing...")
        refresh_result = refresh_access_token()
        if refresh_result.get("success"):
            return True

    # If we still don't have an access token
    if not current_access_token:
        print("[ERROR] No valid Salesmsg tokens found!")
        print("Please ensure SALESMSG_REFRESH_TOKEN is set in .env")
        return False

    return True

def get_auth_headers():
    """Get authorization headers with current token"""
    if not current_access_token:
        ensure_valid_token()

    return {
        "Authorization": f"Bearer {current_access_token}",
        "Content-Type": "application/json"
    }

async def make_authenticated_request(method, url, **kwargs):
    """Make an authenticated request with automatic token refresh on 401"""
    headers = get_auth_headers()
    kwargs['headers'] = headers

    async with httpx.AsyncClient() as client:
        if method.upper() == "POST":
            response = await client.post(url, **kwargs)
        elif method.upper() == "GET":
            response = await client.get(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        # If unauthorized, try to refresh token and retry once
        if response.status_code == 401:
            print("[WARN] 401 Unauthorized - refreshing token...")
            refresh_result = refresh_access_token()
            if refresh_result.get("success"):
                headers = get_auth_headers()
                kwargs['headers'] = headers
                
                if method.upper() == "POST":
                    response = await client.post(url, **kwargs)
                elif method.upper() == "GET":
                    response = await client.get(url, **kwargs)

        return response


class SalesmsgClient:
    def __init__(self):
        self.base_url = SALESMSG_BASE_URL
        self.team_id = SALESMSG_TEAM_ID
        
        # Initialize tokens on first use
        if not current_access_token:
            print("[INFO] Initializing Salesmsg OAuth tokens...")
            if ensure_valid_token():
                print("[INFO] ✅ Salesmsg OAuth tokens ready!")
            else:
                print("[ERROR] ❌ Failed to initialize Salesmsg tokens")

    async def send_sms(self, phone_number: str, message: str) -> dict:
        """Send SMS using OAuth-refreshed tokens"""
        send_url = f"{self.base_url}/messages"
        
        params = {
            "number": phone_number,
            "team_id": self.team_id,
            "message": message
        }

        print(f"[DEBUG] Sending SMS to {phone_number}")

        response = await make_authenticated_request("POST", send_url, params=params)
        
        print(f"[DEBUG] SMS response status: {response.status_code}")
        
        response.raise_for_status()
        return response.json()