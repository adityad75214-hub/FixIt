import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.errors import DuplicateKeyError
from app.core.database import get_database
from app.core.security import get_current_user, require_roles, get_password_hash
from app.core.audit import record_audit_log
from app.models.institution import InstitutionCreate, InstitutionResponse, InstitutionAdminCreate, InstitutionUpdate

router = APIRouter(prefix="/institutions", tags=["Institution Onboarding"])


@router.get("", response_model=list[InstitutionResponse])
async def list_active_institutions():
    db = get_database()
    docs = await db.institutions.find({"status": "active"}).sort("name", 1).to_list(None)
    return [InstitutionResponse(id=str(d["_id"]), name=d["name"], slug=d["slug"], email_domains=d.get("email_domains", []), status=d.get("status", "active")) for d in docs]


@router.post("", response_model=InstitutionResponse, status_code=status.HTTP_201_CREATED)
async def create_institution(payload: InstitutionCreate, current_user: dict = Depends(require_roles("platform_admin"))):
    db = get_database()
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
    return InstitutionResponse(id=institution_id, name=payload.name, slug=payload.slug, email_domains=payload.email_domains, status="active")


@router.post("/{institution_id}/admins", status_code=status.HTTP_201_CREATED)
async def create_institution_admin(institution_id: str, payload: InstitutionAdminCreate, current_user: dict = Depends(require_roles("platform_admin"))):
    db = get_database()
    institution = await db.institutions.find_one({"_id": institution_id, "status": "active"})
    if not institution:
        raise HTTPException(status_code=404, detail="Active institution not found.")
    email = payload.email.strip().lower()
    domain = email.rsplit("@", 1)[-1] if "@" in email else ""
    allowed_domains = institution.get("email_domains", [])
    if allowed_domains and domain not in allowed_domains:
        raise HTTPException(status_code=400, detail="The administrator email must use an approved institution domain.")
    user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
    user = {
        "_id": user_id, "email": email, "password_hash": get_password_hash(payload.password),
        "name": payload.name, "role": "admin", "institution_id": institution_id,
        "department": "Administration", "specialization": [], "is_active": True,
        "token_version": 0, "created_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        await db.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None
    await record_audit_log(action="INSTITUTION_ADMIN_CREATED", resource_type="user", resource_id=user_id, actor=current_user, details={"institution_id": institution_id, "email": email})
    return {"id": user_id, "email": email, "name": payload.name, "role": "admin", "institution_id": institution_id}



@router.put("/{institution_id}", response_model=InstitutionResponse)
async def update_institution(institution_id: str, payload: InstitutionUpdate, current_user: dict = Depends(require_roles("platform_admin"))):
    db = get_database()
    update = {key: value for key, value in payload.model_dump().items() if value is not None}
    if not update:
        raise HTTPException(status_code=400, detail="Provide at least one institution field to update.")
    result = await db.institutions.update_one({"_id": institution_id}, {"$set": update})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Institution not found.")
    institution = await db.institutions.find_one({"_id": institution_id})
    await record_audit_log(action="INSTITUTION_UPDATED", resource_type="institution", resource_id=institution_id, actor=current_user, details={"updated_fields": sorted(update.keys())})
    return InstitutionResponse(id=institution_id, name=institution["name"], slug=institution["slug"], email_domains=institution.get("email_domains", []), status=institution.get("status", "active"))
