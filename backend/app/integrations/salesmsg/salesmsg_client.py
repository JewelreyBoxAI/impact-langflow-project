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
token_expires_at = 0

def load_tokens():
    """Load tokens from persistent storage"""
    global current_access_token, current_refresh_token, token_expires_at

    try:
        if TOKEN_FILE.exists():
            with open(TOKEN_FILE, 'r') as f:
                tokens = json.load(f)
                current_access_token = tokens.get('access_token')
                current_refresh_token = tokens.get('refresh_token')
                
                # Calculate expiration time
                created_at = tokens.get('created_at', 0)
                expires_in = tokens.get('expires_in', 86340)
                token_expires_at = created_at + expires_in
                
                # Check if token is still valid (with 5 min buffer)
                time_left = token_expires_at - time.time()
                if time_left > 300:  # More than 5 minutes left
                    print(f"[DEBUG] ✅ Cached token valid for {int(time_left/60)} more minutes")
                    return True
                else:
                    print(f"[DEBUG] ⚠️ Cached token expired or expiring soon, will refresh")
                    current_access_token = None  # Force refresh
                    return False
    except Exception as e:
        print(f"[WARN] Failed to load tokens: {e}")

    # Fallback to environment variables
    if SALESMSG_REFRESH_TOKEN:
        current_refresh_token = SALESMSG_REFRESH_TOKEN
        print(f"[DEBUG] Using refresh token from environment")

    return current_refresh_token is not None

def save_tokens(access_token=None, refresh_token=None, expires_in=None):
    """Save tokens to persistent storage"""
    global current_access_token, current_refresh_token, token_expires_at

    if access_token:
        current_access_token = access_token
    if refresh_token:
        current_refresh_token = refresh_token

    created_at = int(time.time())
    expires_in = expires_in or 86340
    
    token_data = {
        "access_token": current_access_token,
        "refresh_token": current_refresh_token,
        "created_at": created_at,
        "expires_in": expires_in
    }
    
    # Update global expiration time
    token_expires_at = created_at + expires_in

    try:
        # Ensure parent directory exists
        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with open(TOKEN_FILE, 'w') as f:
            json.dump(token_data, f, indent=2)
        print(f"[INFO] ✅ Tokens saved (valid for {int(expires_in/3600)} hours)")
    except Exception as e:
        print(f"[ERROR] Failed to save tokens: {e}")

def refresh_access_token():
    """Refresh the Salesmsg access token using refresh token (synchronous)"""
    global current_access_token, current_refresh_token

    if not current_refresh_token:
        return {"error": "No refresh token available. Need to complete OAuth setup first."}

    print("[INFO] Refreshing Salesmsg access token...")
    
    data = {
        "grant_type": "refresh_token",
        "client_id": SALESMSG_CLIENT_ID,
        "client_secret": SALESMSG_CLIENT_SECRET,
        "refresh_token": current_refresh_token
    }

    try:
        # Use synchronous httpx Client for token refresh
        with httpx.Client() as client:
            response = client.post(f"{SALESMSG_BASE_URL}/oauth/token", data=data, timeout=10)
        
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data.get("access_token")
            new_refresh_token = token_data.get("refresh_token")
            
            # CRITICAL: Save the NEW refresh token if provided
            if new_refresh_token:
                print("[WARN] ⚠️ New refresh token received - consider updating .env!")
                print(f"SALESMSG_REFRESH_TOKEN={new_refresh_token}")
            
            save_tokens(
                access_token=new_access_token, 
                refresh_token=new_refresh_token or current_refresh_token,
                expires_in=token_data.get("expires_in")
            )
            
            print("[INFO] ✅ Token refreshed successfully")
            return {"success": True, "token": new_access_token}
        else:
            print(f"[ERROR] Refresh failed: {response.status_code} - {response.text}")
            return {"error": f"Token refresh failed: {response.text}"}
    except Exception as e:
        print(f"[ERROR] Token refresh error: {str(e)}")
        return {"error": f"Token refresh error: {str(e)}"}

def ensure_valid_token():
    """Ensure we have a valid access token, refresh if expired"""
    global current_access_token, current_refresh_token

    # Try to load existing tokens and check expiration
    tokens_loaded = load_tokens()
    
    # If token is expired or doesn't exist, refresh it
    if not current_access_token and current_refresh_token:
        print("[INFO] Token missing or expired, refreshing...")
        refresh_result = refresh_access_token()
        if refresh_result.get("success"):
            return True
        else:
            print(f"[ERROR] Refresh failed: {refresh_result.get('error')}")
            return False

    # If we still don't have an access token
    if not current_access_token:
        print("[ERROR] No valid Salesmsg tokens found!")
        print("Please ensure SALESMSG_REFRESH_TOKEN is set in .env")
        return False

    return True

def get_auth_headers():
    """Get authorization headers with current token"""
    # Always check token validity before getting headers
    ensure_valid_token()

    if not current_access_token:
        raise Exception("No valid access token available")

    return {
        "Authorization": f"Bearer {current_access_token}",
        "Content-Type": "application/json"
    }

async def make_authenticated_request(method, url, **kwargs):
    """Make an authenticated request with automatic token refresh on 401/403"""
    headers = get_auth_headers()
    kwargs['headers'] = headers

    async with httpx.AsyncClient() as client:
        if method.upper() == "POST":
            response = await client.post(url, **kwargs)
        elif method.upper() == "GET":
            response = await client.get(url, **kwargs)
        else:
            raise ValueError(f"Unsupported method: {method}")

        # If unauthorized or forbidden, refresh and retry once
        if response.status_code in [401, 403]:
            print(f"[WARN] {response.status_code} error - token may be invalid, refreshing...")
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

        response = await make_authenticated_request("POST", send_url, params=params, timeout=10)
        
        print(f"[DEBUG] SMS response status: {response.status_code}")
        
        response.raise_for_status()
        return response.json()