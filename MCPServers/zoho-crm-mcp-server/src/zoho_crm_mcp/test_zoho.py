import requests

# Get fresh token
response = requests.post(
    "https://accounts.zoho.com/oauth/v2/token",
    data={
        "refresh_token": "1000.6281d839190bc98f9c5c7f5c58caa150.e0b2ea5a06f4cc3de164896330a7ccae",
        "client_id": "1000.58LVTQ2HYAP0VW7DB814U5OC2TE55Y",
        "client_secret": "289c8c0b64f2ee062e93dd6b3e27043fe4575618af",
        "grant_type": "refresh_token"
    }
)

access_token = response.json().get("access_token")
print(f"Got token: {access_token[:30]}...\n")

# Test /users endpoint
print("Testing /users endpoint...")
api_response = requests.get(
    "https://www.zohoapis.com/crm/v2/users",
    headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
    params={"type": "ActiveUsers", "per_page": 1}
)
print(f"Status: {api_response.status_code}")
print(f"Response: {api_response.text[:500]}")

# If that fails, try Leads (you have ZohoCRM.modules.ALL)
print("\n\nTesting /Leads endpoint...")
leads_response = requests.get(
    "https://www.zohoapis.com/crm/v2/Leads",
    headers={"Authorization": f"Zoho-oauthtoken {access_token}"},
    params={"per_page": 1}
)
print(f"Status: {leads_response.status_code}")
print(f"Response: {leads_response.text[:500]}")