import asyncio
import logging
import secrets
import hmac
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr, Field
from pymongo.errors import DuplicateKeyError

from app.core.config import settings
from app.core.database import get_database
from app.core.security import get_password_hash, create_access_token, create_refresh_token
from app.core.audit import record_audit_log
from app.models.user import Token, UserResponse
from app.api.auth import enforce_trusted_origin, set_refresh_cookie

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/registration", tags=["College Email Registration"])

CODE_TTL_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60
MAX_CODE_ATTEMPTS = 5


class RegistrationRequest(BaseModel):
    institution_slug: str = Field(..., min_length=2, max_length=60)
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr = Field(..., max_length=254)
    role: str = Field(..., pattern="^(student|faculty)$")
    department: str = Field(..., min_length=2, max_length=100)
    identifier: str = Field(..., min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=30)


class VerifyRegistrationCode(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
    password: str = Field(..., min_length=12, max_length=128)


def _email_domain(email: str) -> str:
    return email.rsplit("@", 1)[-1].lower()


@router.post("/request-code", status_code=status.HTTP_202_ACCEPTED)
async def request_registration_code(payload: RegistrationRequest, request: Request):
    enforce_trusted_origin(request)
    if not settings.PUBLIC_REGISTRATION_ENABLED:
        raise HTTPException(status_code=403, detail="Self-registration is currently disabled. Contact your institution administrator.")

    if not settings.SMTP_HOST or not (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME) or not settings.APP_BASE_URL:
        raise HTTPException(status_code=503, detail="College email verification is not configured yet. Please contact FixIt support.")

    db = get_database()
    email = str(payload.email).strip().lower()
    identifier = payload.identifier.strip().upper()
    institution = await db.institutions.find_one({"slug": payload.institution_slug.lower(), "status": "active"})
    if not institution:
        raise HTTPException(status_code=404, detail="The selected institution is unavailable.")

    role_domains = institution.get(f"{payload.role}_email_domains") or institution.get("email_domains", [])
    allowed_domains = [str(domain).lower().lstrip("@") for domain in role_domains]
    if not allowed_domains or _email_domain(email) not in allowed_domains:
        raise HTTPException(status_code=403, detail=f"Use an approved {payload.role} email domain for this institution.")

    identifier_pattern = institution.get(f"{payload.role}_identifier_pattern")
    if identifier_pattern:
        import re
        try:
            valid_identifier = re.fullmatch(identifier_pattern, payload.identifier.strip(), flags=re.IGNORECASE) is not None
        except re.error:
            raise HTTPException(status_code=500, detail="This institution's identifier rule is misconfigured. Contact its administrator.") from None
        if not valid_identifier:
            raise HTTPException(status_code=422, detail=f"The {payload.role} ID does not match this institution's required format.")

    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in instead.")

    identifier_query = {
        "institution_id": str(institution["_id"]),
        "role": payload.role,
        "identifier": identifier,
    }
    if await db.users.find_one(identifier_query):
        raise HTTPException(status_code=409, detail=f"This {payload.role} ID is already registered in the selected institution.")

    if await db.pending_registrations.find_one({
        **identifier_query,
        "email": {"$ne": email},
    }):
        raise HTTPException(status_code=409, detail=f"A registration for this {payload.role} ID is already pending verification.")

    now = datetime.now(timezone.utc)
    existing_pending = await db.pending_registrations.find_one({"email": email})
    if existing_pending:
        sent_at = existing_pending.get("code_sent_at", now)
        if isinstance(sent_at, str):
            sent_at = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        if (now - sent_at).total_seconds() < RESEND_COOLDOWN_SECONDS:
            raise HTTPException(status_code=429, detail="A verification code was sent recently. Please wait before requesting another.")

    code = f"{secrets.randbelow(1_000_000):06d}"
    pending_id = f"REG-{uuid.uuid4().hex[:12].upper()}"
    pending = {
        "_id": pending_id,
        "institution_id": str(institution["_id"]),
        "institution_slug": institution["slug"],
        "name": payload.name.strip(),
        "email": email,
        "role": payload.role,
        "department": payload.department.strip(),
        "identifier": identifier,
        "phone": payload.phone,
        "code_hash": __import__("hashlib").sha256((settings.SECRET_KEY + ":" + code).encode("utf-8")).hexdigest(),
        "attempts": 0,
        "created_at": now,
        "code_sent_at": now,
        "expires_at": now + timedelta(minutes=CODE_TTL_MINUTES),
    }
    await db.pending_registrations.delete_one({"email": email})
    try:
        await db.pending_registrations.insert_one(pending)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=409,
            detail=f"This {payload.role} ID already has a pending registration in the selected institution.",
        ) from None

    from app.services.notification_service import _send_email
    body = (
        f"Hello {payload.name},\n\n"
        f"Your FixIt verification code for {institution['name']} is: {code}\n\n"
        f"This code expires in {CODE_TTL_MINUTES} minutes and can be used only once. "
        "If you did not request this, ignore this email.\n\n"
        "FixIt Campus Support"
    )
    try:
        await asyncio.to_thread(_send_email, email, f"Verify your college email — {institution['name']}", body)
    except Exception:
        logger.exception("FixIt registration verification email delivery failed")
        await db.pending_registrations.delete_one({"_id": pending_id})
        raise HTTPException(
            status_code=502,
            detail="We could not send the verification email. Check the address or try again later."
        ) from None

    return {"message": "Verification code sent to your college email.", "email": email, "expires_in_minutes": CODE_TTL_MINUTES}


@router.post("/verify-code", response_model=Token, status_code=status.HTTP_201_CREATED)
async def verify_registration_code(payload: VerifyRegistrationCode, request: Request, response: Response):
    enforce_trusted_origin(request)
    if not settings.PUBLIC_REGISTRATION_ENABLED:
        raise HTTPException(status_code=403, detail="Self-registration is currently disabled.")

    db = get_database()
    email = str(payload.email).strip().lower()
    pending = await db.pending_registrations.find_one({"email": email})
    now = datetime.now(timezone.utc)
    if not pending:
        raise HTTPException(status_code=400, detail="No pending registration was found. Request a new verification code.")

    expires_at = pending.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= now:
        await db.pending_registrations.delete_one({"_id": pending["_id"]})
        raise HTTPException(status_code=400, detail="The verification code has expired. Request a new code.")

    if pending.get("attempts", 0) >= MAX_CODE_ATTEMPTS:
        await db.pending_registrations.delete_one({"_id": pending["_id"]})
        raise HTTPException(status_code=429, detail="Too many incorrect codes. Start registration again.")

    import hashlib
    submitted_hash = hashlib.sha256((settings.SECRET_KEY + ":" + payload.code).encode("utf-8")).hexdigest()
    if not hmac.compare_digest(submitted_hash, pending.get("code_hash", "")):
        await db.pending_registrations.update_one({"_id": pending["_id"]}, {"$inc": {"attempts": 1}})
        raise HTTPException(status_code=400, detail="Incorrect verification code.")

    institution = await db.institutions.find_one({"_id": pending["institution_id"], "status": "active"})
    approved_domains = (institution.get(f"{pending['role']}_email_domains") or institution.get("email_domains", [])) if institution else []
    if not institution or _email_domain(email) not in [str(d).lower().lstrip("@") for d in approved_domains]:
        await db.pending_registrations.delete_one({"_id": pending["_id"]})
        raise HTTPException(status_code=403, detail="Institution email verification is no longer valid.")

    duplicate_identifier = await db.users.find_one({
        "institution_id": pending["institution_id"],
        "role": pending["role"],
        "identifier": pending["identifier"],
    })
    if duplicate_identifier:
        await db.pending_registrations.delete_one({"_id": pending["_id"]})
        raise HTTPException(status_code=409, detail=f"This {pending['role']} ID is already registered in the selected institution.")

    consumed = await db.pending_registrations.delete_one({"_id": pending["_id"], "code_hash": submitted_hash})
    if getattr(consumed, "deleted_count", 0) != 1:
        raise HTTPException(status_code=409, detail="This verification code has already been used. Request a new code.")

    user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
    user = {
        "_id": user_id,
        "email": email,
        "password_hash": get_password_hash(payload.password),
        "name": pending["name"],
        "role": pending["role"],
        "department": pending["department"],
        "phone": pending.get("phone"),
        "identifier": pending["identifier"],
        "specialization": [],
        "is_active": True,
        "email_verified": True,
        "email_verified_at": now.isoformat(),
        "approval_method": "institution_email_otp",
        "membership_verification_status": "email_verified",
        "membership_verification_note": "College email domain and mailbox verified. No institution directory was available for a separate enrollment match.",
        "institution_id": pending["institution_id"],
        "token_version": 0,
        "created_at": now.isoformat(),
    }
    try:
        await db.users.insert_one(user)
    except DuplicateKeyError:
        await db.pending_registrations.delete_one({"_id": pending["_id"]})
        if await db.users.find_one({"email": email}):
            raise HTTPException(status_code=409, detail="An account with this email already exists. Please sign in.") from None
        raise HTTPException(
            status_code=409,
            detail=f"This {pending['role']} ID is already registered in the selected institution.",
        ) from None

    await record_audit_log(
        action="USER_REGISTERED_EMAIL_VERIFIED",
        resource_type="user",
        resource_id=user_id,
        actor={"id": user_id, "name": user["name"], "email": email, "role": user["role"], "institution_id": user["institution_id"]},
        details={"institution_id": user["institution_id"], "verification_method": "institution_email_otp", "membership_status": "email_verified"},
    )

    access_token = create_access_token(data={"sub": user_id, "role": user["role"], "ver": 0})
    raw_refresh, refresh_hash, refresh_exp = create_refresh_token()
    await db.refresh_tokens.insert_one({"user_id": user_id, "token_hash": refresh_hash, "expires_at": refresh_exp, "created_at": now})
    set_refresh_cookie(response, raw_refresh)

    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user_id,
            email=email,
            name=user["name"],
            role=user["role"],
            department=user["department"],
            phone=user.get("phone"),
            identifier=user["identifier"],
            specialization=[],
            is_active=True,
            created_at=user["created_at"],
            institution_id=user["institution_id"],
            institution_name=institution.get("name"),
        ),
    )
