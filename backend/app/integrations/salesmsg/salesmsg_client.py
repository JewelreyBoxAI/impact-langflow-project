import httpx
import time
import os
import json
from pathlib import Path

# Use a simple file in the same directory to cache the token
TOKEN_FILE = Path(__file__).parent / "salesmsg_token_cache.json"

class SalesmsgClient:
    def __init__(self):
        self.base_url = os.getenv("SALESMSG_BASE_URL", "https://api.salesmessage.com/pub/v2.2")
        self.team_id = os.getenv("SALESMSG_TEAM_ID", "186244")
        self.access_token = None # Will be loaded asynchronously

    def _save_token(self, token_data: dict):
        try:
            token_data['expires_at'] = time.time() + token_data['expires_in']
            with open(TOKEN_FILE, 'w') as f:
                json.dump(token_data, f)
        except IOError as e:
            print(f"Error saving token file: {e}")


    def _load_token(self) -> dict | None:
        if not TOKEN_FILE.exists():
            return None
        try:
            with open(TOKEN_FILE, 'r') as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading token file: {e}")
            return None

    async def _refresh_token(self) -> str:
        print("Salesmsg token expired or missing. Refreshing...")
        refresh_url = f"{self.base_url}/oauth/token"
        payload = {
            "grant_type": "refresh_token",
            "client_id": os.getenv("SALESMSG_CLIENT_ID"),
            "client_secret": os.getenv("SALESMSG_CLIENT_SECRET"),
            "refresh_token": os.getenv("SALESMSG_REFRESH_TOKEN")
        }
        headers = {"Content-Type": "application/x-www-form-urlencoded"}

        async with httpx.AsyncClient() as client:
            response = await client.post(refresh_url, data=payload, headers=headers)
            response.raise_for_status()
            new_token_data = response.json()
            self._save_token(new_token_data)
            print("Salesmsg token refreshed successfully.")
            return new_token_data["access_token"]

    async def _get_valid_token(self) -> str:
        token_data = self._load_token()
        if not token_data or time.time() > (token_data.get('expires_at', 0) - 60):
            self.access_token = await self._refresh_token()
        elif not self.access_token:
             self.access_token = token_data["access_token"]
        
        print("Existing Salesmsg token is valid.")
        return self.access_token

    async def send_sms(self, phone_number: str, message: str) -> dict:
        # Ensure we have a valid token before proceeding
        self.access_token = await self._get_valid_token()

        send_url = f"{self.base_url}/messages"
        params = {
            "number": phone_number,
            "team_id": self.team_id,
            "message": message
        }
        headers = {"Authorization": f"Bearer {self.access_token}"}

        async with httpx.AsyncClient() as client:
            response = await client.post(send_url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()