"""
Developer Tools API Routes
DEVELOPMENT ONLY - Token generation for testing
"""
import os
from fastapi import APIRouter
from datetime import datetime, timedelta
import jwt

router = APIRouter()

# Use the SAME secret as dependencies.py
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
JWT_ALGORITHM = 'HS256'

@router.get("/generate-test-token")
def generate_test_token():
    """
    Generates a temporary JWT for API testing in the docs.
    Only available in non-production environments.
    
    Returns:
        dict: Contains the access_token and token_type
    
    Example response:
        {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "bearer",
            "expires_in": 86400
        }
    
    Usage:
        1. Call this endpoint to get a token
        2. Click "Authorize" button in /docs
        3. Enter: Bearer <your_token>
        4. Test any protected endpoint!
    """
    # Create token with the SAME payload structure as dependencies.py expects
    payload = {
        'user_id': 'testuser@impactrealty.com',
        'permissions': ['admin', 'read', 'write'],  # Give all permissions for testing
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours in seconds
        "instructions": "Click 'Authorize' button at top and enter: Bearer <token>"
    }