import re
import uuid
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.core.database import get_database
from app.core.security import get_current_user, require_roles, get_password_hash
from app.core.audit import record_audit_log
from app.core.tenancy import institution_id_for, scoped_filter, tenant_document
from app.models.user import UserResponse, UserCreate, UserUpdate, UserRole

router = APIRouter(prefix="/users", tags=["User Management"])

@router.get("", response_model=List[UserResponse])
async def list_users(
    role: Optional[str] = None,
    search: Optional[str] = Query(default=None, max_length=100),
    department: Optional[str] = Query(default=None, max_length=100),
    is_active: Optional[bool] = None,
    skip: int = Query(0, ge=0, le=100000),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    query = {"institution_id": institution_id_for(current_user)}
    if role:
        query["role"] = role
    if department:
        query["department"] = department
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"email": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"identifier": {"$regex": re.escape(search[:100]), "$options": "i"}}
        ]

    users = await db.users.find(query).skip(skip).limit(limit).to_list(limit)
    response = []
    for u in users:
        # compute active tickets count for staff
        u_id = str(u["_id"])
        active_tickets = 0
        if u.get("role") == "staff":
            active_tickets = await db.tickets.count_documents({
                "institution_id": institution_id_for(current_user),
                "assigned_to.id": u_id,
                "status": {"$in": ["assigned", "in_progress", "on_hold"]}
            })
        response.append(UserResponse(
            id=u_id,
            email=u["email"],
            name=u["name"],
            role=u["role"],
            department=u.get("department"),
            phone=u.get("phone"),
            identifier=u.get("identifier"),
            specialization=u.get("specialization") or [],
            is_active=u.get("is_active", True),
            created_at=u.get("created_at", ""),
            active_tickets_count=active_tickets,
            institution_id=u.get("institution_id") or institution_id_for(current_user)
        ))
    return response

@router.get("/staff", response_model=List[UserResponse])
async def list_staff_members(current_user: dict = Depends(require_roles("admin"))):
    """Returns active IT staff members and workload to administrators."""
    db = get_database()
    staff_users = await db.users.find(scoped_filter(current_user, {"role": "staff", "is_active": True})).to_list(None)
    response = []
    for u in staff_users:
        u_id = str(u["_id"])
        active_tickets = await db.tickets.count_documents({
            "institution_id": institution_id_for(current_user),
            "assigned_to.id": u_id,
            "status": {"$in": ["assigned", "in_progress", "on_hold"]}
        })
        response.append(UserResponse(
            id=u_id,
            email=u["email"],
            name=u["name"],
            role=u["role"],
            department=u.get("department"),
            phone=u.get("phone"),
            identifier=u.get("identifier"),
            specialization=u.get("specialization") or [],
            is_active=u.get("is_active", True),
            created_at=u.get("created_at", ""),
            active_tickets_count=active_tickets,
        institution_id=u.get("institution_id") or institution_id_for(current_user)
        ))
    return response

@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user_by_admin(
    user_in: UserCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    if user_in.role.value == "platform_admin":
        raise HTTPException(status_code=403, detail="Platform administrator accounts can only be provisioned through the platform operations process.")
    if user_in.role.value in {"admin", "staff"}:
        raise HTTPException(status_code=403, detail="Administrator and staff accounts must be provisioned through an approved invitation workflow.")
    existing = await db.users.find_one({"email": user_in.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    user_id = f"USR-{uuid.uuid4().hex[:10].upper()}"
    new_user = {
        "_id": user_id,
        "email": user_in.email.lower(),
        "password_hash": get_password_hash(user_in.password),
        "name": user_in.name,
        "role": user_in.role.value,
        "department": user_in.department,
        "phone": user_in.phone,
        "identifier": user_in.identifier,
        "specialization": user_in.specialization or [],
        "is_active": True,
        "institution_id": institution_id_for(current_user),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    try:
        await db.users.insert_one(new_user)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None

    await record_audit_log(
        action="USER_CREATED_BY_ADMIN",
        resource_type="user",
        resource_id=user_id,
        actor=current_user,
        details={"name": new_user["name"], "role": new_user["role"], "email": new_user["email"]}
    )

    return UserResponse(
        id=user_id,
        email=new_user["email"],
        name=new_user["name"],
        role=new_user["role"],
        department=new_user["department"],
        phone=new_user["phone"],
        identifier=new_user["identifier"],
        specialization=new_user["specialization"],
        is_active=True,
        created_at=new_user["created_at"],
        institution_id=new_user["institution_id"]
    )

@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_admin(
    user_id: str,
    update_data: UserUpdate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    user = await db.users.find_one(scoped_filter(current_user, {"_id": user_id}))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.get("role") == "admin" and user_id == current_user["id"] and update_data.is_active is False:
        raise HTTPException(status_code=400, detail="You cannot deactivate or demote your own administrator account.")
    if user.get("role") == "admin" and (update_data.is_active is not None or update_data.role is not None):
        raise HTTPException(status_code=403, detail="Use Administrator Governance to transfer, deactivate, or reactivate administrator access.")
    if update_data.role is not None and update_data.role.value == "admin" and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Administrator access must be granted through the invitation workflow.")

    if update_data.role is not None and update_data.role.value == "platform_admin":
        raise HTTPException(status_code=403, detail="College administrators cannot grant platform administrator access.")

    update_dict = {}
    if update_data.name is not None:
        update_dict["name"] = update_data.name
    if update_data.phone is not None:
        update_dict["phone"] = update_data.phone
    if update_data.department is not None:
        update_dict["department"] = update_data.department
    if update_data.specialization is not None:
        update_dict["specialization"] = update_data.specialization
    if update_data.is_active is not None:
        update_dict["is_active"] = update_data.is_active
    if update_data.role is not None:
        update_dict["role"] = update_data.role.value

    if update_dict:
        await db.users.update_one(scoped_filter(current_user, {"_id": user_id}), {"$set": update_dict})
        user = await db.users.find_one(scoped_filter(current_user, {"_id": user_id}))

    await record_audit_log(
        action="USER_UPDATED_BY_ADMIN",
        resource_type="user",
        resource_id=user_id,
        actor=current_user,
        details=update_dict
    )

    return UserResponse(
        id=user_id,
        email=user["email"],
        name=user["name"],
        role=user["role"],
        department=user.get("department"),
        phone=user.get("phone"),
        identifier=user.get("identifier"),
        specialization=user.get("specialization") or [],
        is_active=user.get("is_active", True),
        created_at=user.get("created_at", ""),
        institution_id=user.get("institution_id") or institution_id_for(current_user)
    )
