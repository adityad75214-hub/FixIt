import uuid
import re
import secrets
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from app.core.database import get_database
from app.core.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    hash_token,
    get_current_user
)
from app.core.audit import record_audit_log
from app.models.user import UserCreate, UserLogin, UserResponse, Token, PasswordChange, UserUpdate, UserPreferences

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Database-backed sliding-window counters work across backend workers and restarts.
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW_SECONDS = 60


async def _ensure_login_rate_window(db, key: str, window_seconds: int):
    now = datetime.now(timezone.utc)
    doc = await db.login_rate_limits.find_one({"_id": key})
    if doc is None:
        try:
            await db.login_rate_limits.insert_one({
                "_id": key,
                "attempts": 0,
                "window_started_at": now,
                "window_expires_at": now + timedelta(seconds=window_seconds),
            })
        except DuplicateKeyError:
            pass
        doc = await db.login_rate_limits.find_one({"_id": key})

    if doc is None:
        raise HTTPException(status_code=503, detail="Login protection is temporarily unavailable. Please retry shortly.")

    window_started = doc.get("window_started_at", now)
    if isinstance(window_started, str):
        try:
            window_started = datetime.fromisoformat(window_started.replace("Z", "+00:00"))
        except ValueError:
            window_started = now - timedelta(seconds=window_seconds)
    if window_started.tzinfo is None:
        window_started = window_started.replace(tzinfo=timezone.utc)

    if (now - window_started).total_seconds() >= window_seconds:
        await db.login_rate_limits.update_one(
            {"_id": key, "window_started_at": doc.get("window_started_at")},
            {"$set": {
                "attempts": 0,
                "window_started_at": now,
                "window_expires_at": now + timedelta(seconds=window_seconds),
            }},
        )
        doc = await db.login_rate_limits.find_one({"_id": key})

    return doc


async def check_login_rate_limit(db, key: str, max_attempts: int = LOGIN_RATE_LIMIT, window_seconds: int = LOGIN_RATE_WINDOW_SECONDS):
    """Reject requests after too many failures; successful logins do not consume quota."""
    doc = await _ensure_login_rate_window(db, key, window_seconds)
    if doc.get("attempts", 0) >= max_attempts:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Please wait before trying again.",
            headers={"Retry-After": str(window_seconds)},
        )


async def record_login_failure(db, key: str, max_attempts: int = LOGIN_RATE_LIMIT, window_seconds: int = LOGIN_RATE_WINDOW_SECONDS):
    """Count only failed credentials, using a compare-and-set window to avoid stale increments."""
    for _ in range(2):
        doc = await _ensure_login_rate_window(db, key, window_seconds)
        updated = await db.login_rate_limits.find_one_and_update(
            {"_id": key, "window_started_at": doc.get("window_started_at")},
            {"$inc": {"attempts": 1}},
            return_document=ReturnDocument.AFTER,
        )
        if updated is not None:
            if updated.get("attempts", 0) > max_attempts:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many failed login attempts. Please wait before trying again.",
                    headers={"Retry-After": str(window_seconds)},
                )
            return
    raise HTTPException(status_code=503, detail="Login protection is temporarily unavailable. Please retry shortly.")


async def clear_login_rate_limits(db, *keys: str) -> None:
    await db.login_rate_limits.delete_many({"_id": {"$in": list(keys)}})


def set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key="fixit_refresh_token",
        value=raw_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.COOKIE_SAMESITE.lower(),
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    # Remove both the scoped cookie and the older root-path cookie from previous builds.
    for cookie_path in ("/api/auth", "/"):
        response.delete_cookie(
            key="fixit_refresh_token",
            path=cookie_path,
            secure=settings.refresh_cookie_secure,
            httponly=True,
            samesite=settings.COOKIE_SAMESITE.lower(),
        )


def enforce_trusted_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    allowed = {item.rstrip("/") for item in settings.BACKEND_CORS_ORIGINS}
    if origin and origin.rstrip("/") not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Untrusted request origin.")


def refresh_token_is_expired(token_doc: dict) -> bool:
    expires_at = token_doc.get("expires_at")
    if not expires_at:
        return True
    if isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
        except ValueError:
            return True
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at <= datetime.now(timezone.utc)

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, response: Response, request: Request):
    enforce_trusted_origin(request)
    if not settings.PUBLIC_REGISTRATION_ENABLED or settings.is_production:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Public registration is disabled. Contact your college IT administrator to request an account.")
    db = get_database()

    # Resolve workspace from an approved institution slug; never accept a raw institution ID.
    institution_id = "INST-DEFAULT"
    if user_in.institution_slug:
        institution = await db.institutions.find_one({"slug": user_in.institution_slug.lower(), "status": "active"})
        if not institution:
            raise HTTPException(status_code=400, detail="That college workspace was not found or is not active.")
        domain = user_in.email.lower().rsplit("@", 1)[-1]
        approved_domains = institution.get("email_domains", [])
        if str(institution["_id"]) != "INST-DEFAULT":
            if not approved_domains:
                raise HTTPException(status_code=403, detail="This college workspace requires an administrator-issued account invitation.")
            if domain not in approved_domains:
                raise HTTPException(status_code=403, detail="Use your college email address to join this institution.")
        institution_id = str(institution["_id"])

    # Check if user already exists
    existing = await db.users.find_one({"email": user_in.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    # Faculty, staff and admin accounts must be provisioned by an administrator.
    if user_in.role != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only student accounts can register publicly. Faculty, IT Staff and Admin accounts are provisioned by an Administrator."
        )

    user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
    new_user = {
        "_id": user_id,
        "email": user_in.email.lower(),
        "password_hash": get_password_hash(user_in.password),
        "name": user_in.name,
        "role": user_in.role.value if hasattr(user_in.role, "value") else user_in.role,
        "department": user_in.department,
        "phone": user_in.phone,
        "identifier": user_in.identifier,
        "specialization": [],
        "is_active": True,
        "institution_id": institution_id,
        "token_version": 0,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    try:
        await db.users.insert_one(new_user)
    except DuplicateKeyError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.") from None

    await record_audit_log(
        action="USER_REGISTER",
        resource_type="user",
        resource_id=user_id,
        actor={"id": user_id, "name": new_user["name"], "email": new_user["email"], "role": new_user["role"], "institution_id": institution_id},
        details={"email": new_user["email"], "role": new_user["role"]}
    )

    access_token = create_access_token(data={"sub": user_id, "role": new_user["role"], "ver": 0})
    raw_refresh, refresh_hash, refresh_exp = create_refresh_token()

    # Store hashed refresh token server-side
    await db.refresh_tokens.insert_one({
        "user_id": user_id,
        "token_hash": refresh_hash,
        "expires_at": refresh_exp,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Set rotating httpOnly SameSite cookie
    set_refresh_cookie(response, raw_refresh)

    institution_doc = await db.institutions.find_one({"_id": institution_id})
    user_response = UserResponse(
        id=user_id,
        email=new_user["email"],
        name=new_user["name"],
        role=new_user["role"],
        department=new_user["department"],
        phone=new_user["phone"],
        identifier=new_user["identifier"],
        specialization=[],
        is_active=True,
        created_at=new_user["created_at"],
        institution_id=institution_id,
        institution_name=(institution_doc or {}).get("name", "Default Institution"),
        admin_level=new_user.get("admin_level")
    )
    return Token(access_token=access_token, user=user_response)

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, request: Request, response: Response):
    enforce_trusted_origin(request)
    db = get_database()
    client_ip = request.client.host if request.client else "unknown"
    email_key = f"email:{credentials.email.lower()}"
    ip_key = f"ip:{client_ip}"
    await check_login_rate_limit(db, email_key)
    await check_login_rate_limit(db, ip_key)
    user = await db.users.find_one({"email": credentials.email.lower()})

    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        await record_login_failure(db, email_key)
        await record_login_failure(db, ip_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact campus IT administration."
        )
    if user.get("role") != "platform_admin":
        institution = await db.institutions.find_one({"_id": user.get("institution_id") or "INST-DEFAULT"})
        if not institution or institution.get("status", "active") != "active":
            raise HTTPException(status_code=403, detail="This institution workspace is suspended or unavailable.")

    # Clear this account’s failed attempts, but do not let a successful login reset
    # the shared IP failure counter and thereby bypass protection for other accounts.
    await clear_login_rate_limits(db, email_key)

    user_id = str(user["_id"])
    access_token = create_access_token(data={"sub": user_id, "role": user["role"], "ver": user.get("token_version", 0)})
    raw_refresh, refresh_hash, refresh_exp = create_refresh_token()

    # Invalidate previous refresh tokens for rotation hygiene
    await db.refresh_tokens.delete_many({"user_id": user_id})
    await db.refresh_tokens.insert_one({
        "user_id": user_id,
        "token_hash": refresh_hash,
        "expires_at": refresh_exp,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    # Set rotating cookie
    set_refresh_cookie(response, raw_refresh)

    await record_audit_log(
        action="USER_LOGIN",
        resource_type="user",
        resource_id=user_id,
        actor={"id": user_id, "name": user["name"], "email": user["email"], "role": user["role"], "institution_id": user.get("institution_id") or "INST-DEFAULT"},
        details={"login_time": datetime.now(timezone.utc).isoformat()}
    )

    institution_doc = await db.institutions.find_one({"_id": user.get("institution_id") or "INST-DEFAULT"})
    user_response = UserResponse(
        id=user_id,
        email=user["email"],
        name=user["name"],
        role=user["role"],
        department=user.get("department"),
        phone=user.get("phone"),
        identifier=user.get("identifier"),
        specialization=user.get("specialization") or [],
        avatar_url=user.get("avatar_url"),
        is_active=user.get("is_active", True),
        created_at=user.get("created_at", datetime.now(timezone.utc).isoformat()),
        institution_id=user.get("institution_id") or "INST-DEFAULT",
        institution_name=(institution_doc or {}).get("name", "Default Institution"),
        admin_level=user.get("admin_level")
    )
    return Token(access_token=access_token, user=user_response)

@router.post("/refresh", response_model=Token)
async def refresh_access_token(request: Request, response: Response):
    enforce_trusted_origin(request)
    raw_refresh = request.cookies.get("fixit_refresh_token")
    if not raw_refresh:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token cookie provided."
        )

    token_hash = hash_token(raw_refresh)
    db = get_database()
    token_doc = await db.refresh_tokens.find_one({"token_hash": token_hash})
    if not token_doc or refresh_token_is_expired(token_doc):
        if token_doc:
            await db.refresh_tokens.delete_one({"_id": token_doc.get("_id")})
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    # Consume the presented token atomically. Only one concurrent refresh can succeed.
    consumed = await db.refresh_tokens.delete_one({"_id": token_doc["_id"], "token_hash": token_hash})
    if getattr(consumed, "deleted_count", 0) != 1:
        clear_refresh_cookie(response)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token has already been used.")

    user = await db.users.find_one({"_id": token_doc["user_id"]})
    if not user or not user.get("is_active", True):
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account no longer active."
        )
    if user.get("role") != "platform_admin":
        institution = await db.institutions.find_one({"_id": user.get("institution_id") or "INST-DEFAULT"})
        if not institution or institution.get("status", "active") != "active":
            clear_refresh_cookie(response)
            raise HTTPException(status_code=403, detail="This institution workspace is suspended or unavailable.")

    # Rotate refresh token after the old token has been consumed.
    new_raw, new_hash, new_exp = create_refresh_token()
    await db.refresh_tokens.insert_one({
        "user_id": str(user["_id"]),
        "token_hash": new_hash,
        "expires_at": new_exp,
        "created_at": datetime.now(timezone.utc).isoformat()
    })

    set_refresh_cookie(response, new_raw)

    access_token = create_access_token(data={"sub": str(user["_id"]), "role": user["role"], "ver": user.get("token_version", 0)})
    institution_doc = await db.institutions.find_one({"_id": user.get("institution_id") or "INST-DEFAULT"})
    user_response = UserResponse(
        id=str(user["_id"]),
        email=user["email"],
        name=user["name"],
        role=user["role"],
        department=user.get("department"),
        phone=user.get("phone"),
        identifier=user.get("identifier"),
        specialization=user.get("specialization") or [],
        avatar_url=user.get("avatar_url"),
        is_active=user.get("is_active", True),
        created_at=user.get("created_at", datetime.now(timezone.utc).isoformat()),
        institution_id=user.get("institution_id") or "INST-DEFAULT",
        institution_name=(institution_doc or {}).get("name", "Default Institution")
    )
    return Token(access_token=access_token, user=user_response)

@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    current_user: dict = Depends(get_current_user),
):
    enforce_trusted_origin(request)
    db = get_database()

    # Revoke every access token issued before logout and every refresh session.
    # Access tokens carry the user's token_version, which get_current_user checks.
    await db.users.update_one(
        {"_id": current_user["id"]},
        {"$inc": {"token_version": 1}},
    )
    await db.refresh_tokens.delete_many({"user_id": current_user["id"]})

    await record_audit_log(
        action="USER_LOGOUT",
        resource_type="user",
        resource_id=current_user["id"],
        actor=current_user,
        details={"status": "success"},
    )
    clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        name=current_user["name"],
        role=current_user["role"],
        department=current_user.get("department"),
        phone=current_user.get("phone"),
        identifier=current_user.get("identifier"),
        specialization=current_user.get("specialization") or [],
        avatar_url=current_user.get("avatar_url"),
        is_active=current_user.get("is_active", True),
        created_at=current_user.get("created_at", ""),
        institution_id=current_user.get("institution_id") or "INST-DEFAULT",
        institution_name=current_user.get("institution_name"),
        admin_level=current_user.get("admin_level")
    )

@router.put("/profile", response_model=UserResponse)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    update_dict = {}
    if update_data.name:
        update_dict["name"] = update_data.name
    if update_data.phone is not None:
        update_dict["phone"] = update_data.phone
    if update_data.department is not None:
        update_dict["department"] = update_data.department
    if update_data.avatar_url is not None:
        avatar = update_data.avatar_url.strip()
        if avatar and not (avatar.startswith("https://") or re.fullmatch(r"/api/uploads/[a-f0-9]{32}", avatar)):
            raise HTTPException(status_code=400, detail="Profile image URL must use HTTPS.")
        update_dict["avatar_url"] = avatar or None
    if update_data.specialization is not None and current_user["role"] in ["staff", "admin"]:
        update_dict["specialization"] = update_data.specialization

    if update_dict:
        await db.users.update_one({"_id": current_user["id"]}, {"$set": update_dict})
        updated = await db.users.find_one({"_id": current_user["id"]})
    else:
        updated = current_user

    return UserResponse(
        id=current_user["id"],
        email=updated["email"],
        name=updated["name"],
        role=updated["role"],
        department=updated.get("department"),
        phone=updated.get("phone"),
        identifier=updated.get("identifier"),
        specialization=updated.get("specialization") or [],
        avatar_url=updated.get("avatar_url"),
        is_active=updated.get("is_active", True),
        created_at=updated.get("created_at", ""),
        institution_id=updated.get("institution_id") or "INST-DEFAULT",
        institution_name=current_user.get("institution_name"),
        admin_level=updated.get("admin_level")
    )

@router.post("/change-password")
async def change_password(
    data: PasswordChange,
    response: Response,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    user = await db.users.find_one({"_id": current_user["id"]})
    if not verify_password(data.current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    await db.users.update_one(
        {"_id": current_user["id"]},
        {"$set": {"password_hash": get_password_hash(data.new_password)}, "$inc": {"token_version": 1}}
    )
    # A password change revokes every refresh session for this account.
    await db.refresh_tokens.delete_many({"user_id": current_user["id"]})
    clear_refresh_cookie(response)

    await record_audit_log(
        action="PASSWORD_CHANGE",
        resource_type="user",
        resource_id=current_user["id"],
        actor=current_user,
        details={"status": "success"}
    )
    return {"message": "Password changed successfully"}




class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., max_length=254)


class PasswordResetConfirm(BaseModel):
    token: str = Field(..., min_length=32, max_length=256)
    new_password: str = Field(..., min_length=12, max_length=128)


@router.post("/password-reset/request")
async def request_password_reset(payload: PasswordResetRequest, request: Request):
    enforce_trusted_origin(request)
    db = get_database()
    email = str(payload.email).strip().lower()
    generic = {"message": "If an account exists for that email, a password reset link will be sent."}
    user = await db.users.find_one({"email": email})
    if not user or not user.get("is_active", True) or not settings.APP_BASE_URL:
        return generic

    now = datetime.now(timezone.utc)
    recent = await db.password_reset_tokens.find_one({
        "user_id": str(user["_id"]),
        "created_at": {"$gt": now - timedelta(seconds=60)},
    })
    if recent:
        return generic

    raw_token = secrets.token_urlsafe(40)
    token_hash = hash_token(raw_token)
    await db.password_reset_tokens.delete_many({"user_id": str(user["_id"])})
    await db.password_reset_tokens.insert_one({
        "_id": token_hash,
        "user_id": str(user["_id"]),
        "created_at": now,
        "expires_at": now + timedelta(minutes=15),
    })

    from app.services.notification_service import _send_email
    reset_url = f"{settings.APP_BASE_URL.rstrip('/')}/reset-password?token={raw_token}"
    body = (
        f"Hello {user.get('name', 'there')},\n\n"
        f"Use this link to reset your FixIt password (valid for 15 minutes):\n{reset_url}\n\n"
        "If you did not request this, ignore this email."
    )
    try:
        await asyncio.to_thread(_send_email, email, "Reset your FixIt password", body)
    except Exception:
        await db.password_reset_tokens.delete_one({"_id": token_hash})
        logger.exception("FixIt password-reset email delivery failed")
        return generic
    return generic


@router.post("/password-reset/confirm")
async def confirm_password_reset(payload: PasswordResetConfirm, request: Request, response: Response):
    enforce_trusted_origin(request)
    db = get_database()
    token_hash = hash_token(payload.token)
    now = datetime.now(timezone.utc)
    token_doc = await db.password_reset_tokens.find_one({"_id": token_hash})
    if not token_doc:
        raise HTTPException(status_code=400, detail="This password reset link is invalid or has expired. Request a new one.")
    expires_at = token_doc.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        await db.password_reset_tokens.delete_one({"_id": token_hash})
        raise HTTPException(status_code=400, detail="This password reset link is invalid or has expired. Request a new one.")

    consumed = await db.password_reset_tokens.delete_one({"_id": token_hash, "expires_at": token_doc.get("expires_at")})
    if getattr(consumed, "deleted_count", 0) != 1:
        raise HTTPException(status_code=400, detail="This password reset link has already been used. Request a new one.")

    user_id = token_doc["user_id"]
    updated = await db.users.update_one(
        {"_id": user_id, "is_active": {"$ne": False}},
        {"$set": {"password_hash": get_password_hash(payload.new_password), "password_changed_at": now.isoformat()}, "$inc": {"token_version": 1}},
    )
    if getattr(updated, "modified_count", 0) != 1:
        raise HTTPException(status_code=400, detail="This account is unavailable. Contact your administrator.")
    await db.password_reset_tokens.delete_many({"user_id": user_id})
    await db.refresh_tokens.delete_many({"user_id": user_id})
    clear_refresh_cookie(response)
    await record_audit_log(
        action="PASSWORD_RESET",
        resource_type="user",
        resource_id=user_id,
        actor={"id": user_id, "role": "system", "name": "Password reset"},
        details={"status": "success"},
    )
    return {"message": "Your password has been reset. You can now sign in."}


@router.get("/preferences")
async def get_my_preferences(current_user: dict = Depends(get_current_user)):
    db = get_database()
    doc = await db.user_preferences.find_one({"user_id": current_user["id"], "institution_id": current_user.get("institution_id") or "INST-DEFAULT"}) or {}
    return {
        "email_notifications": doc.get("email_notifications", True),
        "in_app_notifications": doc.get("in_app_notifications", True),
        "language": doc.get("language", "en"),
    }


@router.put("/preferences")
async def update_my_preferences(
    preferences: UserPreferences,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    values = preferences.model_dump()
    await db.user_preferences.update_one(
        {"user_id": current_user["id"], "institution_id": current_user.get("institution_id") or "INST-DEFAULT"},
        {"$set": {**values, "institution_id": current_user.get("institution_id") or "INST-DEFAULT", "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True,
    )
    return values
