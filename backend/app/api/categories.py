import uuid
import re
from pymongo.errors import DuplicateKeyError
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.security import require_roles, get_current_user
from app.core.audit import record_audit_log
from app.core.tenancy import institution_id_for, scoped_filter
from app.models.category import CategoryResponse, CategoryCreate, CampusLocationResponse, CampusLocationBase

router = APIRouter(prefix="/categories", tags=["Categories & Locations"])

@router.get("", response_model=List[CategoryResponse])
async def list_categories(include_inactive: bool = False, current_user: dict = Depends(get_current_user)):
    db = get_database()
    query = {"institution_id": institution_id_for(current_user)}
    if not include_inactive:
        query["is_active"] = True
    docs = await db.categories.find(query).to_list(None)
    return [
        CategoryResponse(
            id=str(d["_id"]),
            name=d["name"],
            description=d.get("description"),
            subcategories=d.get("subcategories", []),
            is_active=d.get("is_active", True),
            icon=d.get("icon", "Wrench")
        )
        for d in docs
    ]

@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    cat_in: CategoryCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    existing = await db.categories.find_one({"institution_id": institution_id_for(current_user), "name": {"$regex": f"^{re.escape(cat_in.name.strip())}$", "$options": "i"}})
    if existing:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    cat_id = f"CAT-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "_id": cat_id,
        "name": cat_in.name,
        "description": cat_in.description,
        "subcategories": cat_in.subcategories,
        "is_active": cat_in.is_active,
        "icon": cat_in.icon or "Wrench",
        "institution_id": institution_id_for(current_user)
    }
    await db.categories.insert_one(doc)

    await record_audit_log(
        action="CATEGORY_CREATED",
        resource_type="category",
        resource_id=cat_id,
        actor=current_user,
        details={"name": cat_in.name}
    )

    return CategoryResponse(id=cat_id, **cat_in.model_dump())

@router.put("/{cat_id}", response_model=CategoryResponse)
async def update_category(
    cat_id: str,
    cat_in: CategoryCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    existing = await db.categories.find_one(scoped_filter(current_user, {"_id": cat_id}))
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    duplicate = await db.categories.find_one({
        "name": {"$regex": f"^{re.escape(cat_in.name.strip())}$", "$options": "i"},
        "_id": {"$ne": cat_id},
        "institution_id": institution_id_for(current_user),
    })
    if duplicate:
        raise HTTPException(status_code=409, detail="Another category already uses this name.")

    try:
        await db.categories.update_one(
            {"_id": cat_id, "institution_id": institution_id_for(current_user)},
            {"$set": cat_in.model_dump()}
        )
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Another category already uses this name.") from None

    await record_audit_log(
        action="CATEGORY_UPDATED",
        resource_type="category",
        resource_id=cat_id,
        actor=current_user,
        details={"name": cat_in.name, "is_active": cat_in.is_active}
    )

    return CategoryResponse(id=cat_id, **cat_in.model_dump())

@router.get("/locations", response_model=List[CampusLocationResponse])
async def list_campus_locations(current_user: dict = Depends(get_current_user)):
    db = get_database()
    docs = await db.campus_locations.find(scoped_filter(current_user, {"is_active": True})).to_list(None)
    return [
        CampusLocationResponse(
            id=str(d["_id"]),
            building=d["building"],
            floors=d.get("floors", ["Ground", "1st", "2nd", "3rd"]),
            rooms=d.get("rooms", []),
            is_active=d.get("is_active", True)
        )
        for d in docs
    ]

@router.post("/locations", response_model=CampusLocationResponse, status_code=status.HTTP_201_CREATED)
async def create_campus_location(
    loc_in: CampusLocationBase,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    loc_id = f"LOC-{uuid.uuid4().hex[:8].upper()}"
    doc = {
        "_id": loc_id,
        "building": loc_in.building,
        "floors": loc_in.floors,
        "rooms": loc_in.rooms,
        "is_active": loc_in.is_active,
        "institution_id": institution_id_for(current_user)
    }
    await db.campus_locations.insert_one(doc)
    return CampusLocationResponse(id=loc_id, **loc_in.model_dump())
