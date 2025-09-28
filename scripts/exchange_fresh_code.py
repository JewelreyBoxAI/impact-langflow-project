#!/usr/bin/env python3
"""
Exchange Fresh Zoho Authorization Code for Tokens
Uses the exact credentials and process from your specification
"""

import requests
import json
import sys
import os
from pathlib import Path

# Your exact credentials
ZOHO_CLIENT_ID = "1000.58LVTQ2HYAP0VW7DB814U5OC2TE55Y"
ZOHO_CLIENT_SECRET = "289c8c0b64f2ee062e93dd6b3e27043fe4575618af"
ZOHO_REDIRECT_URI = "https://localhost"

def exchange_code_for_tokens(auth_code):
    """Exchange authorization code for access and refresh tokens"""

    print("Exchanging Zoho Authorization Code for Tokens")
    print("=" * 50)
    print(f"Client ID: {ZOHO_CLIENT_ID}")
    print(f"Auth Code: {auth_code[:20]}...")
    print(f"Redirect URI: {ZOHO_REDIRECT_URI}")
    print()

    token_url = "https://accounts.zoho.com/oauth/v2/token"

    data = {
        'code': auth_code,
        'redirect_uri': ZOHO_REDIRECT_URI,
        'client_id': ZOHO_CLIENT_ID,
        'client_secret': ZOHO_CLIENT_SECRET,
        'grant_type': 'authorization_code'
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        print("Making token exchange request...")
        response = requests.post(token_url, data=data, headers=headers)

        print(f"Response Status: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()

            print()
            print("SUCCESS: Token exchange completed!")
            print("=" * 50)
            print(f"Access Token: {token_data.get('access_token', 'N/A')[:30]}...")
            print(f"Refresh Token: {token_data.get('refresh_token', 'N/A')[:30]}...")
            print(f"API Domain: {token_data.get('api_domain', 'N/A')}")
            print(f"Token Type: {token_data.get('token_type', 'N/A')}")
            print(f"Expires In: {token_data.get('expires_in', 'N/A')} seconds")

            # Create .env content
            env_content = f"""# Zoho OAuth2 Credentials - WORKING TOKENS
ZOHO_CLIENT_ID={ZOHO_CLIENT_ID}
ZOHO_CLIENT_SECRET={ZOHO_CLIENT_SECRET}
ZOHO_REFRESH_TOKEN={token_data.get('refresh_token', '')}
ZOHO_CRM_BASE_URL={token_data.get('api_domain', 'https://www.zohoapis.com')}/crm/v2
ZOHO_AUTH_URL=https://accounts.zoho.com/oauth/v2/token

# Current Access Token (expires in {token_data.get('expires_in', 3600)} seconds)
ZOHO_ACCESS_TOKEN={token_data.get('access_token', '')}

# MCP Configuration
ZOHO_AUTH_MODE=refresh_token
ZOHO_TOKEN_REFRESH_ENABLED=true

# Salesmsg API
SALESMG_API_TOKEN=EQXpWTbq315gGMRZfgro96TOG8iGBXWb09zz8vyb
"""

            # Save to .env file
            env_file = Path(__file__).parent.parent / '.env.zoho_working'
            with open(env_file, 'w') as f:
                f.write(env_content)

            print()
            print(f"Credentials saved to: {env_file}")
            print()
            print("To activate:")
            print(f"1. Copy {env_file} to .env")
            print("2. Test with: python scripts/test_zoho_connection.py")
            print("3. Start MCP server")

            # Test the access token immediately
            print()
            print("Testing access token...")
            test_api_access(token_data.get('access_token'), token_data.get('api_domain'))

            return token_data

        else:
            print(f"TOKEN EXCHANGE FAILED: {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except Exception as e:
        print(f"ERROR: {e}")
        return None

def test_api_access(access_token, api_domain):
    """Test API access with the new token"""
    try:
        test_url = f"{api_domain}/crm/v2/users"
        headers = {
            'Authorization': f'Zoho-oauthtoken {access_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(test_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            print(f"API TEST SUCCESS: Found {len(users)} users")

            if users:
                user = users[0]
                print(f"Current User: {user.get('full_name', 'Unknown')}")
                print(f"Email: {user.get('email', 'Unknown')}")

            print()
            print("FINAL RESULT: MFA BYPASS IS WORKING!")
            print("FINAL RESULT: Zoho MCP connection OPERATIONAL!")

        else:
            print(f"API TEST FAILED: {response.status_code}")
            print(f"Response: {response.text[:200]}")

    except Exception as e:
        print(f"API TEST ERROR: {e}")

def generate_auth_url():
    """Generate the authorization URL"""
    auth_url = f"https://accounts.zoho.com/oauth/v2/auth?scope=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL&response_type=code&access_type=offline&client_id={ZOHO_CLIENT_ID}&redirect_uri={ZOHO_REDIRECT_URI}"
    return auth_url

def main():
    if len(sys.argv) != 2:
        print("Zoho OAuth2 Token Exchange")
        print("=" * 30)
        print()
        print("Usage: python exchange_fresh_code.py <authorization_code>")
        print()
        print("To get a fresh authorization code:")
        print("1. Visit this URL in your browser:")
        print()
        print(generate_auth_url())
        print()
        print("2. Click 'Accept' to authorize")
        print("3. Copy the code from the redirect URL")
        print("4. Run this script with the code")
        print()
        print("The redirect URL will look like:")
        print("https://localhost?code=FRESH_CODE_HERE")
        sys.exit(1)

    auth_code = sys.argv[1]

    if not auth_code.startswith('1000.'):
        print("ERROR: Invalid authorization code format")
        print("Expected format: 1000.xxxxx.xxxxx")
        sys.exit(1)

    tokens = exchange_code_for_tokens(auth_code)

    if tokens:
        print()
        print("🎉 SUCCESS: OAuth2 setup complete!")
        print("🎉 MFA bypass is now operational!")
    else:
        print()
        print("❌ FAILED: Could not exchange authorization code")
        print("Get a fresh code and try again")
        sys.exit(1)

if __name__ == "__main__":
    main()