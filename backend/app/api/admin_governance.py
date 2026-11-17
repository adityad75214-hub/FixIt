import asyncio
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from pymongo.errors import DuplicateKeyError

from app.core.audit import record_audit_log
from app.core.config import settings
from app.core.database import get_database
from app.core.security import get_current_user, hash_token, require_roles

router = APIRouter(prefix="/institutions", tags=["Institution Administrator Governance"])


class AdminRequestPayload(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr = Field(..., max_length=254)
    designation: str | None = Field(default=None, max_length=120)
    department: str | None = Field(default=None, max_length=100)


class AdminStatusPayload(BaseModel):
    is_active: bool


async def _institution_or_404(db, institution_id: str):
    institution = await db.institutions.find_one({"_id": institution_id, "status": "active"})
    if not institution:
        raise HTTPException(status_code=404, detail="Active institution not found.")
    return institution


async def _assert_institution_scope(current_user: dict, institution_id: str):
    if current_user.get("role") != "platform_admin" and current_user.get("institution_id") != institution_id:
        raise HTTPException(status_code=403, detail="You can manage administrators only in your own institution.")


async def _assert_primary(current_user: dict, institution_id: str):
    await _assert_institution_scope(current_user, institution_id)
    if current_user.get("role") != "platform_admin" and current_user.get("admin_level") != "primary":
        raise HTTPException(status_code=403, detail="Only the Primary College Admin can approve or manage administrators.")


def _check_domain(email: str, institution: dict):
    domain = email.rsplit("@", 1)[-1].lower()
    allowed = [str(item).lower().lstrip("@") for item in institution.get("email_domains", [])]
    if not allowed or domain not in allowed:
        raise HTTPException(status_code=400, detail="The administrator email must use an approved institution domain.")


async def _send_admin_invitation(db, institution: dict, request_doc: dict, actor: dict, admin_level: str = "college"):
    if not settings.SMTP_HOST or not settings.APP_BASE_URL or not (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME):
        raise HTTPException(status_code=503, detail="Administrator invitations require SMTP_HOST, sender email, and APP_BASE_URL configuration.")

    email = request_doc["email"].strip().lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    existing = await db.admin_invitations.find_one({
        "email": email, "institution_id": str(institution["_id"]), "used_at": None,
        "expires_at": {"$gt": datetime.now(timezone.utc)}
    })
    if existing:
        raise HTTPException(status_code=409, detail="A valid invitation already exists for this email.")

    raw_token = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    invitation_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    invitation = {
        "_id": invitation_id, "email": email, "name": request_doc["name"],
        "role": "admin", "admin_level": admin_level,
        "department": request_doc.get("department") or "Administration",
        "designation": request_doc.get("designation"),
        "institution_id": str(institution["_id"]), "token_hash": hash_token(raw_token),
        "created_at": now, "expires_at": now + timedelta(hours=48),
        "created_by": actor["id"], "used_at": None,
    }
    await db.admin_invitations.insert_one(invitation)
    invite_url = settings.APP_BASE_URL.rstrip("/") + "/accept-invitation?token=" + raw_token
    body = (
        f"Hello {request_doc['name']},\n\nYou have been invited to administer {institution['name']} on FixIt. "
        "This single-use invitation expires in 48 hours.\n\n"
        f"Accept your invitation: {invite_url}\n\nIf you were not expecting this invitation, ignore this email."
    )
    try:
        from app.services.notification_service import _send_email
        await asyncio.to_thread(_send_email, email, f"FixIt administrator invitation — {institution['name']}", body)
    except Exception:
        await db.admin_invitations.delete_one({"_id": invitation_id})
        raise HTTPException(status_code=502, detail="The invitation email could not be sent. No account was created.") from None
    return invitation_id


@router.get("/{institution_id}/administrators")
async def list_institution_administrators(
    institution_id: str,
    current_user: dict = Depends(require_roles("platform_admin", "admin")),
):
    await _assert_institution_scope(current_user, institution_id)
    db = get_database()
    await _institution_or_404(db, institution_id)
    users = await db.users.find({"institution_id": institution_id, "role": "admin"}).sort("created_at", 1).to_list(None)
    return [{
        "id": str(user["_id"]), "name": user.get("name", ""), "email": user.get("email", ""),
        "admin_level": user.get("admin_level", "college"), "is_active": user.get("is_active", True),
        "created_at": user.get("created_at", ""),
    } for user in users]


@router.post("/{institution_id}/admin-requests", status_code=status.HTTP_202_ACCEPTED)
async def request_additional_administrator(
    institution_id: str,
    payload: AdminRequestPayload,
    current_user: dict = Depends(require_roles("admin")),
):
    await _assert_institution_scope(current_user, institution_id)
    if current_user.get("admin_level") == "primary":
        raise HTTPException(status_code=400, detail="Primary Admins can invite administrators directly; requests are for other College Admins.")
    db = get_database()
    institution = await _institution_or_404(db, institution_id)
    email = str(payload.email).strip().lower()
    _check_domain(email, institution)
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    pending = await db.admin_requests.find_one({"institution_id": institution_id, "email": email, "status": "pending"})
    if pending:
        raise HTTPException(status_code=409, detail="A pending administrator request already exists for this email.")
    request_id = f"ARQ-{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc)
    request_doc = {
        "_id": request_id, "institution_id": institution_id, "name": payload.name.strip(),
        "email": email, "designation": payload.designation, "department": payload.department,
        "status": "pending", "requested_by": current_user["id"], "created_at": now,
    }
    await db.admin_requests.insert_one(request_doc)
    await record_audit_log(
        action="INSTITUTION_ADMIN_REQUESTED", resource_type="admin_request",
        resource_id=request_id, actor=current_user,
        details={"institution_id": institution_id, "email": email},
    )
    return {"message": "Administrator request submitted for Primary Admin approval.", "request_id": request_id}


@router.get("/{institution_id}/admin-requests")
async def list_admin_requests(
    institution_id: str,
    current_user: dict = Depends(require_roles("platform_admin", "admin")),
):
    await _assert_primary(current_user, institution_id)
    db = get_database()
    await _institution_or_404(db, institution_id)
    rows = await db.admin_requests.find({"institution_id": institution_id, "status": "pending"}).sort("created_at", 1).to_list(None)
    return [{
        "id": row["_id"], "name": row["name"], "email": row["email"],
        "designation": row.get("designation"), "department": row.get("department"),
        "requested_by": row.get("requested_by"), "created_at": row.get("created_at"),
    } for row in rows]


@router.post("/{institution_id}/admin-requests/{request_id}/approve", status_code=status.HTTP_200_OK)
async def approve_admin_request(
    institution_id: str,
    request_id: str,
    current_user: dict = Depends(require_roles("platform_admin", "admin")),
):
    await _assert_primary(current_user, institution_id)
    db = get_database()
    institution = await _institution_or_404(db, institution_id)
    request_doc = await db.admin_requests.find_one({"_id": request_id, "institution_id": institution_id, "status": "pending"})
    if not request_doc:
        raise HTTPException(status_code=404, detail="Pending administrator request not found.")
    _check_domain(request_doc["email"], institution)
    invitation_id = await _send_admin_invitation(db, institution, request_doc, current_user, "college")
    updated = await db.admin_requests.update_one(
        {"_id": request_id, "institution_id": institution_id, "status": "pending"},
        {"$set": {"status": "approved", "reviewed_by": current_user["id"], "reviewed_at": datetime.now(timezone.utc), "invitation_id": invitation_id}},
    )
    if updated.modified_count != 1:
        await db.admin_invitations.delete_one({"_id": invitation_id})
        raise HTTPException(status_code=409, detail="This request was already reviewed.")
    await record_audit_log(
        action="INSTITUTION_ADMIN_REQUEST_APPROVED", resource_type="admin_request",
        resource_id=request_id, actor=current_user,
        details={"email": request_doc["email"], "invitation_id": invitation_id},
    )
    return {"message": "Request approved. A single-use invitation has been emailed.", "email": request_doc["email"]}


@router.post("/{institution_id}/admin-requests/{request_id}/reject")
async def reject_admin_request(
    institution_id: str,
    request_id: str,
    current_user: dict = Depends(require_roles("platform_admin", "admin")),
):
    await _assert_primary(current_user, institution_id)
    db = get_database()
    await _institution_or_404(db, institution_id)
    result = await db.admin_requests.update_one(
        {"_id": request_id, "institution_id": institution_id, "status": "pending"},
        {"$set": {"status": "rejected", "reviewed_by": current_user["id"], "reviewed_at": datetime.now(timezone.utc)}},
    )
    if result.modified_count != 1:
        raise HTTPException(status_code=404, detail="Pending administrator request not found.")
    await record_audit_log(
        action="INSTITUTION_ADMIN_REQUEST_REJECTED", resource_type="admin_request",
        resource_id=request_id, actor=current_user, details={},
    )
    return {"message": "Administrator request rejected."}


@router.patch("/{institution_id}/administrators/{user_id}")
async def update_administrator_status(
    institution_id: str,
    user_id: str,
    payload: AdminStatusPayload,
    current_user: dict = Depends(require_roles("platform_admin", "admin")),
):
    await _assert_primary(current_user, institution_id)
    db = get_database()
    await _institution_or_404(db, institution_id)
    target = await db.users.find_one({"_id": user_id, "institution_id": institution_id, "role": "admin"})
    if not target:
        raise HTTPException(status_code=404, detail="Administrator not found in this institution.")
    if target.get("admin_level") == "primary":
        raise HTTPException(status_code=409, detail="The Primary Admin cannot be deactivated here. Transfer primary ownership first.")
    if target.get("is_active", True) == payload.is_active:
        return {"message": "No change required.", "is_active": payload.is_active}
    await db.users.update_one(
        {"_id": user_id, "institution_id": institution_id, "role": "admin", "admin_level": {"$ne": "primary"}},
        {"$set": {"is_active": payload.is_active, "updated_at": datetime.now(timezone.utc).isoformat()}, "$inc": {"token_version": 1}},
    )
    await db.refresh_tokens.delete_many({"user_id": user_id})
    await record_audit_log(
        action="INSTITUTION_ADMIN_ACTIVATED" if payload.is_active else "INSTITUTION_ADMIN_DEACTIVATED",
        resource_type="user", resource_id=user_id, actor=current_user,
        details={"email": target.get("email"), "is_active": payload.is_active},
    )
    return {"message": "Administrator status updated.", "is_active": payload.is_active}


@router.post("/{institution_id}/administrators/{user_id}/make-primary")
async def make_primary_administrator(
    institution_id: str,
    user_id: str,
    current_user: dict = Depends(require_roles("platform_admin", "admin")),
):
    db = get_database()
    await _assert_primary(current_user, institution_id)
    await _institution_or_404(db, institution_id)
    target = await db.users.find_one({"_id": user_id, "institution_id": institution_id, "role": "admin", "is_active": True})
    if not target:
        raise HTTPException(status_code=404, detail="Active college administrator not found.")
    previous = await db.users.find_one({"institution_id": institution_id, "role": "admin", "admin_level": "primary", "is_active": True})
    if previous and str(previous["_id"]) != user_id:
        await db.users.update_one({"_id": previous["_id"], "admin_level": "primary"}, {"$set": {"admin_level": "college"}})
    await db.users.update_one({"_id": user_id, "institution_id": institution_id, "role": "admin"}, {"$set": {"admin_level": "primary"}})
    await record_audit_log(
        action="PRIMARY_ADMIN_TRANSFERRED", resource_type="institution",
        resource_id=institution_id, actor={**current_user, "institution_id": institution_id},
        details={"previous_primary_admin_id": str(previous["_id"]) if previous else None, "new_primary_admin_id": user_id},
    )
    return {"message": "Primary administrator assignment updated."}
