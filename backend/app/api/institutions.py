import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError
from app.core.database import get_database
from app.core.security import get_current_user, require_roles, get_password_hash
from app.core.audit import record_audit_log
from app.models.institution import InstitutionCreate, InstitutionResponse, InstitutionAdminInvite, InstitutionAdminInviteAccept, InstitutionUpdate
from app.core.security import hash_token

router = APIRouter(prefix="/institutions", tags=["Institution Onboarding"])


@router.get("", response_model=list[InstitutionResponse])
async def list_active_institutions():
    db = get_database()
    docs = await db.institutions.find({"status": "active"}).sort("name", 1).to_list(None)
    return [InstitutionResponse(id=str(d["_id"]), name=d["name"], slug=d["slug"], email_domains=d.get("email_domains", []), student_email_domains=d.get("student_email_domains", []), faculty_email_domains=d.get("faculty_email_domains", []), student_identifier_pattern=d.get("student_identifier_pattern"), faculty_identifier_pattern=d.get("faculty_identifier_pattern"), status=d.get("status", "active")) for d in docs]


@router.get("/manage", response_model=list[InstitutionResponse])
async def list_institutions_for_platform(current_user: dict = Depends(require_roles("platform_admin"))):
    db = get_database()
    docs = await db.institutions.find({}).sort("name", 1).to_list(None)
    return [InstitutionResponse(id=str(d["_id"]), name=d["name"], slug=d["slug"], email_domains=d.get("email_domains", []), student_email_domains=d.get("student_email_domains", []), faculty_email_domains=d.get("faculty_email_domains", []), student_identifier_pattern=d.get("student_identifier_pattern"), faculty_identifier_pattern=d.get("faculty_identifier_pattern"), status=d.get("status", "active")) for d in docs]


@router.post("", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def create_institution(payload: InstitutionCreate, current_user: dict = Depends(require_roles("platform_admin"))):
    db = get_database()
    if payload.email_domains:
        conflicting = await db.institutions.find_one({"email_domains": {"$in": payload.email_domains}})
        if conflicting:
            raise HTTPException(status_code=409, detail="One or more email domains are already assigned to an institution.")
    institution_id = f"INST-{uuid.uuid4().hex[:10].upper()}"
    doc = {"_id": institution_id, **payload.model_dump(), "status": "active", "created_at": datetime.now(timezone.utc).isoformat(), "created_by": current_user["id"]}
    try:
        await db.institutions.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="That institution slug or email domain is already registered.") from None
    # Ensure a default template exists, including installations without demo seeding.
    default_categories = await db.categories.find({"institution_id": "INST-DEFAULT"}).to_list(None)
    if not default_categories:
        from app.seed_reference_data import seed_reference_data
        await seed_reference_data()
        default_categories = await db.categories.find({"institution_id": "INST-DEFAULT"}).to_list(None)
    if default_categories:
        await db.categories.insert_many([
            {**{key: value for key, value in item.items() if key != "_id"}, "_id": f"CAT-{uuid.uuid4().hex[:8].upper()}", "institution_id": institution_id}
            for item in default_categories
        ])
    default_policies = await db.sla_policies.find({"institution_id": "INST-DEFAULT"}).to_list(None)
    if default_policies:
        await db.sla_policies.insert_many([
            {**{key: value for key, value in item.items() if key != "_id"}, "_id": f"SLA-{uuid.uuid4().hex[:8].upper()}", "institution_id": institution_id}
            for item in default_policies
        ])
    await record_audit_log(action="INSTITUTION_CREATED", resource_type="institution", resource_id=institution_id, actor=current_user, details={"name": payload.name, "slug": payload.slug})
    return InstitutionResponse(id=institution_id, name=payload.name, slug=payload.slug, email_domains=payload.email_domains, student_email_domains=payload.student_email_domains, faculty_email_domains=payload.faculty_email_domains, student_identifier_pattern=payload.student_identifier_pattern, faculty_identifier_pattern=payload.faculty_identifier_pattern, status="active")


@router.post("/{institution_id}/admins/invitations", status_code=status.HTTP_202_ACCEPTED)
async def invite_institution_admin(institution_id: str, payload: InstitutionAdminInvite, current_user: dict = Depends(require_roles("platform_admin", "admin"))):
    """Invite a college administrator; the recipient chooses their password after accepting."""
    from app.core.config import settings
    from app.services.notification_service import _send_email

    db = get_database()
    # Platform admins provision the first Primary College Admin. Thereafter,
    # only the Primary College Admin can issue direct invitations.
    if current_user.get("role") != "platform_admin":
        if current_user.get("institution_id") != institution_id:
            raise HTTPException(status_code=403, detail="You can invite administrators only for your own institution.")
        if current_user.get("admin_level") != "primary":
            raise HTTPException(status_code=403, detail="Only the Primary College Admin can send direct administrator invitations. Submit a request for approval instead.")

    institution = await db.institutions.find_one({"_id": institution_id, "status": "active"})
    if not institution:
        raise HTTPException(status_code=404, detail="Active institution not found.")

    if not settings.SMTP_HOST or not settings.APP_BASE_URL or not (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME):
        raise HTTPException(status_code=503, detail="Administrator invitations require SMTP_HOST, sender email, and APP_BASE_URL configuration.")

    email = str(payload.email).strip().lower()
    domain = email.rsplit("@", 1)[-1]
    allowed_domains = [str(item).lower().lstrip("@") for item in institution.get("email_domains", [])]
    if not allowed_domains or domain not in allowed_domains:
        raise HTTPException(status_code=400, detail="The administrator email must use an approved institution domain.")
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    pending_registration = await db.pending_registrations.find_one({"email": email})
    if pending_registration:
        raise HTTPException(status_code=409, detail="This email has a pending student/faculty verification. Finish or let that registration expire before inviting it as an administrator.")
    if await db.admin_invitations.find_one({"email": email, "institution_id": institution_id, "used_at": None, "revoked_at": None, "expires_at": {"$gt": datetime.now(timezone.utc)}}):
        raise HTTPException(status_code=409, detail="A valid invitation already exists for this email.")

    raw_token = __import__("secrets").token_urlsafe(48)
    now = datetime.now(timezone.utc)
    invitation_id = f"INV-{uuid.uuid4().hex[:12].upper()}"
    active_admin_count = await db.users.count_documents({"institution_id": institution_id, "role": "admin", "$or": [{"is_active": True}, {"is_active": {"$exists": False}}]})
    pending_primary = await db.admin_invitations.find_one({"institution_id": institution_id, "admin_level": "primary", "used_at": None, "revoked_at": None, "expires_at": {"$gt": now}})
    invited_admin_level = "primary" if current_user.get("role") == "platform_admin" and active_admin_count == 0 and pending_primary is None else "college"
    invite = {
        "_id": invitation_id,
        "email": email,
        "name": payload.name,
        "role": "admin",
        "admin_level": invited_admin_level,
        "department": payload.department or "Administration",
        "designation": payload.designation,
        "institution_id": institution_id,
        "token_hash": hash_token(raw_token),
        "created_at": now,
        "expires_at": now + timedelta(hours=48),
        "created_by": current_user["id"],
        "used_at": None,
        "revoked_at": None,
    }
    await db.admin_invitations.insert_one(invite)
    invite_url = settings.APP_BASE_URL.rstrip("/") + "/accept-invitation?token=" + raw_token
    body = (
        f"Hello {payload.name},\n\nYou have been invited to administer {institution['name']} on FixIt. "
        f"This invitation expires in 48 hours and can only be used once.\n\n"
        f"Accept your invitation: {invite_url}\n\n"
        "If you were not expecting this invitation, you can ignore this email."
    )
    try:
        await asyncio.to_thread(_send_email, email, f"FixIt administrator invitation — {institution['name']}", body)
    except Exception:
        await db.admin_invitations.delete_one({"_id": invitation_id})
        raise HTTPException(status_code=502, detail="The invitation email could not be sent. No administrator account was created.") from None

    await record_audit_log(action="INSTITUTION_ADMIN_INVITED", resource_type="institution", resource_id=institution_id, actor={**current_user, "institution_id": institution_id}, details={"email": email, "invitation_id": invitation_id, "admin_level": invited_admin_level})
    return {"message": "Administrator invitation sent.", "email": email, "expires_in_hours": 48}


@router.post("/admin-invitations/accept", status_code=status.HTTP_201_CREATED)
async def accept_institution_admin_invitation(payload: InstitutionAdminInviteAccept):
    """Accept a single-use invitation and set the administrator's own password."""
    db = get_database()
    now = datetime.now(timezone.utc)
    invite = await db.admin_invitations.find_one({"token_hash": hash_token(payload.token), "used_at": None, "revoked_at": None, "expires_at": {"$gt": now}})
    if not invite:
        raise HTTPException(status_code=400, detail="This invitation is invalid, expired, or already used.")
    institution = await db.institutions.find_one({"_id": invite["institution_id"], "status": "active"})
    if not institution:
        raise HTTPException(status_code=400, detail="The institution is unavailable. Contact FixIt support.")
    # Administrator access is granted by this verified, single-use invitation.
    # Unlike student/faculty self-registration, invitees may use personal email.
    if await db.users.find_one({"email": invite["email"]}):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    if await db.pending_registrations.find_one({"email": invite["email"], "expires_at": {"$gt": now}}):
        raise HTTPException(
            status_code=409,
            detail="This email has a pending student/faculty verification. Complete or let that registration expire before accepting an administrator invitation.",
        )

    user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
    user = {
        "_id": user_id,
        "email": invite["email"],
        "password_hash": get_password_hash(payload.password),
        "name": invite["name"],
        "role": "admin",
        "admin_level": invite.get("admin_level", "college"),
        "institution_id": invite["institution_id"],
        "department": invite.get("department", "Administration"),
        "designation": invite.get("designation"),
        "specialization": [],
        "is_active": True,
        "email_verified": True,
        "email_verified_at": now.isoformat(),
        "approval_method": "institution_admin_invitation",
        "token_version": 0,
        "created_at": now.isoformat(),
    }
    try:
        await db.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None

    consumed = await db.admin_invitations.update_one(
        {"_id": invite["_id"], "used_at": None, "revoked_at": None, "expires_at": {"$gt": now}},
        {"$set": {"used_at": now, "accepted_by": user_id}},
    )
    if consumed.modified_count != 1:
        await db.users.delete_one({"_id": user_id})
        raise HTTPException(status_code=400, detail="This invitation has already been used.")
    await record_audit_log(action="INSTITUTION_ADMIN_INVITATION_ACCEPTED", resource_type="user", resource_id=user_id, actor={"id": user_id, "email": user["email"], "name": user["name"], "role": "admin", "institution_id": user["institution_id"]}, details={"institution_id": user["institution_id"], "admin_level": user["admin_level"]})
    return {"message": "Administrator account created. You can now sign in.", "user": {"id": user_id, "email": user["email"], "name": user["name"], "role": "admin", "admin_level": user["admin_level"], "institution_id": user["institution_id"]}}



@router.put("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(institution_id: str, payload: InstitutionUpdate, current_user: dict = Depends(require_roles("platform_admin"))):
    db = get_database()
    update = {key: value for key, value in payload.model_dump().items() if value is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Provide at least one institution field to update.")
    if institution_id == "INST-DEFAULT" and update.get("status") == "suspended":
        raise HTTPException(status_code=400, detail="The default migrated workspace cannot be suspended.")
    domains = update.get("email_domains")
    if domains:
        conflicting = await db.institutions.find_one({"_id": {"$ne": institution_id}, "email_domains": {"$in": domains}})
        if conflicting:
            raise HTTPException(status_code=409, detail="One or more email domains are already assigned to another institution.")
    result = await db.institutions.update_one({"_id": institution_id}, {"$set": update})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Institution not found.")
    institution = await db.institutions.find_one({"_id": institution_id})
    await record_audit_log(action="INSTITUTION_UPDATED", resource_type="institution", resource_id=institution_id, actor=current_user, details={"updated_fields": sorted(update.keys())})
    return InstitutionResponse(id=institution_id, name=institution["name"], slug=institution["slug"], email_domains=institution.get("email_domains", []), student_email_domains=institution.get("student_email_domains", []), faculty_email_domains=institution.get("faculty_email_domains", []), student_identifier_pattern=institution.get("student_identifier_pattern"), faculty_identifier_pattern=institution.get("faculty_identifier_pattern"), status=institution.get("status", "active"))
