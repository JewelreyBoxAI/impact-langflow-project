import httpx
import time
import os
import json
from pathlib import Path

TOKEN_FILE = Path(__file__).parent / "salesmsg_pat_cache.json"

# Test file creation on module load
print(f"[DEBUG] Token file path: {TOKEN_FILE}")
print(f"[DEBUG] Token file parent directory: {TOKEN_FILE.parent}")
print(f"[DEBUG] Parent directory exists: {TOKEN_FILE.parent.exists()}")
print(f"[DEBUG] Parent directory writable: {os.access(TOKEN_FILE.parent, os.W_OK)}")

# Try creating a test file
try:
    test_file = TOKEN_FILE.parent / "test_write.txt"
    with open(test_file, 'w') as f:
        f.write("test")
    print(f"[DEBUG] ✅ Test file creation successful")
    test_file.unlink()  # Delete test file
except Exception as e:
    print(f"[ERROR] ❌ Cannot write to directory: {e}")

class SalesmsgClient:
    def __init__(self):
        self.base_url = os.getenv("SALESMSG_BASE_URL", "https://api.salesmessage.com/pub/v2.2")
        self.team_id = os.getenv("SALESMSG_TEAM_ID", "186244")
        self.pat = os.getenv("SALESMSG_PAT")
        self.access_token = None

    def _save_token(self, token_data: dict):
        """Save token with extensive error handling"""
        try:
            print(f"[DEBUG] _save_token called")
            print(f"[DEBUG] Attempting to save to: {TOKEN_FILE}")
            print(f"[DEBUG] Token data keys: {list(token_data.keys())}")
            
            # Ensure parent directory exists
            TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
            print(f"[DEBUG] Parent directory created/verified")
            
            # Add expiration time
            token_data['expires_at'] = time.time() + token_data.get('expires_in', 3600)
            print(f"[DEBUG] Expires at: {token_data['expires_at']}")
            
            # Write file
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f, indent=2)
            
            # Verify file was created
            if TOKEN_FILE.exists():
                file_size = TOKEN_FILE.stat().st_size
                print(f"[DEBUG] ✅ Token file created successfully! Size: {file_size} bytes")
            else:
                print(f"[ERROR] ❌ File does not exist after write!")
                
        except PermissionError as e:
            print(f"[ERROR] ❌ Permission denied writing token file: {e}")
        except IOError as e:
            print(f"[ERROR] ❌ IO error writing token file: {e}")
        except Exception as e:
            print(f"[ERROR] ❌ Unexpected error saving token: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()

    def _load_token(self) -> dict | None:
        """Load token with extensive error handling"""
        print(f"[DEBUG] _load_token called")
        print(f"[DEBUG] Checking file: {TOKEN_FILE}")
        print(f"[DEBUG] File exists: {TOKEN_FILE.exists()}")
        
        if not TOKEN_FILE.exists():
            print("[DEBUG] No token file found")
            return None
            
        try:
            with open(TOKEN_FILE, 'r') as f:
                token_data = json.load(f)
            print(f"[DEBUG] ✅ Token loaded successfully")
            print(f"[DEBUG] Token expires at: {token_data.get('expires_at')}")
            return token_data
        except json.JSONDecodeError as e:
            print(f"[ERROR] ❌ Invalid JSON in token file: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] ❌ Error loading token: {type(e).__name__}: {e}")
            return None

    async def _refresh_pat(self) -> str:
        """Refresh the Personal Access Token"""
        print("[INFO] Refreshing Personal Access Token...")
        refresh_url = f"{self.base_url}/oauth/personal-token/refresh"
        
        # Use current access token to refresh (or initial PAT if first time)
        current_token = self.access_token or self.pat
        
        print(f"[DEBUG] Using token (first 20 chars): {current_token[:20] if current_token else 'None'}")
        
        headers = {
            "Authorization": f"Bearer {current_token}",
            "Content-Type": "application/json"
        }

        try:
            async with httpx.AsyncClient() as client:
                print(f"[DEBUG] POST {refresh_url}")
                response = await client.post(refresh_url, headers=headers)
                
                print(f"[DEBUG] PAT refresh response status: {response.status_code}")
                print(f"[DEBUG] PAT refresh response body: {response.text}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    print(f"[DEBUG] Token data received: {list(token_data.keys())}")
                    
                    new_access_token = token_data.get("access_token")
                    
                    # THIS IS WHERE THE FILE SHOULD BE CREATED
                    print(f"[DEBUG] About to call _save_token...")
                    self._save_token(token_data)
                    print(f"[DEBUG] _save_token completed")
                    
                    print("[INFO] ✅ PAT refreshed successfully")
                    return new_access_token
                else:
                    error_msg = f"PAT refresh failed: {response.status_code} - {response.text}"
                    print(f"[ERROR] {error_msg}")
                    raise Exception(error_msg)
                    
        except Exception as e:
            print(f"[ERROR] PAT refresh exception: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

    async def _get_valid_token(self) -> str:
        """Get a valid access token, refreshing if needed"""
        print("[DEBUG] _get_valid_token called")
        token_data = self._load_token()
        
        # Check if token exists and is still valid (refresh 5 min before expiry)
        if not token_data or time.time() > (token_data.get('expires_at', 0) - 300):
            print("[DEBUG] Token missing or expired, refreshing...")
            self.access_token = await self._refresh_pat()
        elif not self.access_token:
            self.access_token = token_data["access_token"]
            print("[INFO] Existing PAT is valid")
        
        return self.access_token

    async def send_sms(self, phone_number: str, message: str) -> dict:
        """Send SMS using auto-refreshed PAT"""
        print(f"[DEBUG] send_sms called for {phone_number}")
        self.access_token = await self._get_valid_token()

        send_url = f"{self.base_url}/messages"
        params = {
            "number": phone_number,
            "team_id": self.team_id,
            "message": message
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}

        print(f"[DEBUG] Sending SMS to {phone_number}")

        async with httpx.AsyncClient() as client:
            response = await client.post(send_url, params=params, headers=headers)
            
            print(f"[DEBUG] SMS response status: {response.status_code}")
            print(f"[DEBUG] SMS response body: {response.text}")
            
            response.raise_for_status()
            return response.json()