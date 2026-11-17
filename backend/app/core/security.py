import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Any, Tuple
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import settings
from app.core.database import get_database

password_hash = PasswordHash((Argon2Hasher(),))

# Login accepts JSON, so document bearer-token authentication separately.
# Swagger can then accept the access token returned by POST /api/auth/login.
bearer_scheme = HTTPBearer(auto_error=False)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    return password_hash.hash(password)

def hash_token(raw_token: str) -> str:
    """Hash refresh tokens for safe storage server-side."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Short-lived access token: 15 minutes by default
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token() -> Tuple[str, str, datetime]:
    """Generates raw token for client cookie, hash for database, and expiry (7 days)."""
    raw_token = secrets.token_urlsafe(48)
    token_hash = hash_token(raw_token)
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, token_hash, expires_at

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise credentials_exception

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"require": ["exp", "sub", "type"]},
        )
        user_id: str = payload.get("sub")
        if not user_id or payload.get("type") != "access":
            raise credentials_exception
    except (jwt.PyJWTError, TypeError, ValueError):
        raise credentials_exception

    db = get_database()
    user = await db.users.find_one({"_id": user_id})
    if user is None:
        user = await db.users.find_one({"email": user_id})
    if user is None:
        raise credentials_exception

    if not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user account")
    if payload.get("ver", 0) != user.get("token_version", 0):
        raise credentials_exception

    # Keep password hashes out of request-scoped user objects.
    user.pop("password_hash", None)
    user["id"] = str(user.get("_id"))
    return user

def require_roles(*allowed_roles: str):
    async def role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of the following roles: {', '.join(allowed_roles)}"
            )
        return current_user
    return role_checker
