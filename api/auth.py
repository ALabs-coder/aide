#!/usr/bin/env python3
"""
Authentication and authorization module for Lambda
"""

import jwt
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, APIKeyHeader
from pydantic import BaseModel
from config import settings
import logging

logger = logging.getLogger(__name__)

# Security schemes
api_key_header = APIKeyHeader(name=settings.api_key_header, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

class User(BaseModel):
    """User model for authentication"""
    user_id: str
    email: Optional[str] = None
    roles: list = []
    is_active: bool = True

class AuthToken(BaseModel):
    """JWT token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[User]:
    """
    Verify API key authentication
    
    Args:
        api_key: API key from header
        
    Returns:
        User object if valid, None otherwise
        
    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key:
        return None
    
    # Hash the provided API key for comparison (security best practice)
    hashed_key = hashlib.sha256(api_key.encode()).hexdigest()
    
    # In production, store hashed API keys in environment or AWS Secrets Manager
    valid_hashed_keys = [
        hashlib.sha256(key.encode()).hexdigest() 
        for key in settings.valid_api_keys
    ]
    
    if hashed_key not in valid_hashed_keys:
        logger.warning(f"Invalid API key attempt: {api_key[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    # Return user based on API key (in real app, fetch from database)
    return User(
        user_id=f"api_user_{api_key[:8]}",
        roles=["api_user"],
        is_active=True
    )

def create_jwt_token(user: User) -> AuthToken:
    """
    Create JWT token for user
    
    Args:
        user: User object
        
    Returns:
        AuthToken with JWT
    """
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=500,
            detail="JWT secret key not configured"
        )
    
    expires_delta = timedelta(hours=settings.jwt_expiration_hours)
    expire = datetime.utcnow() + expires_delta
    
    payload = {
        "sub": user.user_id,
        "email": user.email,
        "roles": user.roles,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access_token"
    }
    
    token = jwt.encode(
        payload, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    
    return AuthToken(
        access_token=token,
        expires_in=int(expires_delta.total_seconds())
    )

def verify_jwt_token(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme)
) -> Optional[User]:
    """
    Verify JWT token authentication
    
    Args:
        credentials: Bearer token credentials
        
    Returns:
        User object if valid, None otherwise
        
    Raises:
        HTTPException: If token is invalid
    """
    if not credentials or not credentials.credentials:
        return None
    
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=500,
            detail="JWT authentication not configured"
        )
    
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: missing user ID"
            )
        
        return User(
            user_id=user_id,
            email=payload.get("email"),
            roles=payload.get("roles", []),
            is_active=True
        )
        
    except jwt.ExpiredSignatureError:
        logger.warning("Expired JWT token attempt")
        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        logger.warning("Invalid JWT token attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

def get_current_user(
    api_user: Optional[User] = Depends(verify_api_key),
    jwt_user: Optional[User] = Depends(verify_jwt_token)
) -> User:
    """
    Get current authenticated user (supports both API key and JWT)
    
    Args:
        api_user: User from API key auth
        jwt_user: User from JWT auth
        
    Returns:
        Authenticated user
        
    Raises:
        HTTPException: If no valid authentication provided
    """
    user = api_user or jwt_user
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required. Provide valid API key in X-API-KEY header or Bearer token."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="User account is disabled"
        )
    
    logger.info(f"Authenticated user: {user.user_id}")
    return user

def require_role(required_role: str):
    """
    Decorator to require specific role
    
    Args:
        required_role: Required role name
        
    Returns:
        Dependency function
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if required_role not in current_user.roles and "admin" not in current_user.roles:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied. Required role: {required_role}"
            )
        return current_user
    
    return role_checker

# Rate limiting using in-memory cache (for Lambda, consider DynamoDB for persistence)
import time
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.requests = defaultdict(list)
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if user is within rate limits
        
        Args:
            user_id: User identifier
            
        Returns:
            True if allowed, False otherwise
        """
        now = time.time()
        window_start = now - settings.rate_limit_window
        
        # Clean old requests
        self.requests[user_id] = [
            timestamp for timestamp in self.requests[user_id]
            if timestamp > window_start
        ]
        
        # Check if within limit
        if len(self.requests[user_id]) >= settings.rate_limit_requests:
            return False
        
        # Add current request
        self.requests[user_id].append(now)
        return True

rate_limiter = RateLimiter()

def check_rate_limit(current_user: User = Depends(get_current_user)) -> User:
    """
    Check rate limiting for authenticated user
    
    Args:
        current_user: Authenticated user
        
    Returns:
        User if within limits
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    if not rate_limiter.is_allowed(current_user.user_id):
        logger.warning(f"Rate limit exceeded for user: {current_user.user_id}")
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded. Maximum {settings.rate_limit_requests} requests per hour."
        )
    
    return current_user