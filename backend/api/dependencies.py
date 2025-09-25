"""
FastAPI Dependencies
Shared dependencies for API routes with JWT authentication
"""

import os
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Optional

security = HTTPBearer()

# JWT Configuration
JWT_SECRET = os.getenv('JWT_SECRET', 'dev-secret-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24

class AuthService:
    """JWT Authentication service"""

    @staticmethod
    def create_token(user_data: Dict) -> str:
        """Create a JWT token for user"""
        payload = {
            'user_id': user_data.get('user_id', 'system'),
            'permissions': user_data.get('permissions', ['read']),
            'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    """Validate JWT token and return user info"""

    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify JWT token
    user_data = AuthService.verify_token(credentials.credentials)

    # Additional security checks
    if not user_data.get('user_id'):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user_data

def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: Dict = Depends(get_current_user)):
        user_permissions = current_user.get('permissions', [])
        if permission not in user_permissions and 'admin' not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission '{permission}' not found"
            )
        return current_user
    return permission_checker