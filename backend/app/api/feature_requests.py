import uuid
from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.database import get_database
from app.core.security import get_current_user, require_roles
from app.core.audit import record_audit_log

router = APIRouter(prefix="/feature-requests", tags=["Feature Requests & Roadmap"])

FeatureStatus = Literal["submitted", "under_review", "planned", "in_progress", "released", "declined"]


class FeatureRequestCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=100)
    description: str = Field(..., min_length=20, max_length=2000)
    area: str = Field(default="General", min_length=2, max_length=60)

    @field_validator("title", "description", "area")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be blank.")
        return cleaned


class FeatureRequestUpdate(BaseModel):
    status: FeatureStatus
    admin_note: Optional[str] = Field(default=None, max_length=1000)


def _serialize(doc: dict, include_admin_note: bool = False) -> dict:
    result = {
        "id": str(doc.get("_id", "")),
        "title": doc.get("title", ""),
        "description": doc.get("description", ""),
        "area": doc.get("area", "General"),
        "status": doc.get("status", "submitted"),
        "created_by": doc.get("created_by", {}),
        "created_at": doc.get("created_at", ""),
        "updated_at": doc.get("updated_at", ""),
    }
    if include_admin_note:
        result["admin_note"] = doc.get("admin_note")
    return result


@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feature_request(
    payload: FeatureRequestCreate,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    now = datetime.now(timezone.utc).isoformat()
    request_id = f"FTR-{uuid.uuid4().hex[:10].upper()}"
    doc = {
        "_id": request_id,
        "title": payload.title.strip(),
        "description": payload.description.strip(),
        "area": payload.area.strip(),
        "status": "submitted",
        "admin_note": None,
        "created_by": {
            "id": current_user["id"],
            "name": current_user.get("name", "Campus user"),
            "role": current_user.get("role", "student"),
        },
        "created_at": now,
        "updated_at": now,
    }
    await db.feature_requests.insert_one(doc)
    await record_audit_log(
        action="FEATURE_REQUEST_SUBMITTED",
        resource_type="feature_request",
        resource_id=request_id,
        actor=current_user,
        details={"title": doc["title"], "area": doc["area"]},
    )
    return _serialize(doc)


@router.get("")
async def list_feature_requests(current_user: dict = Depends(get_current_user)):
    db = get_database()
    query = {} if current_user.get("role") == "admin" else {"created_by.id": current_user["id"]}
    docs = await db.feature_requests.find(query).sort("created_at", -1).to_list(None)
    return [_serialize(doc, include_admin_note=current_user.get("role") == "admin") for doc in docs]


@router.patch("/{request_id}")
async def update_feature_request(
    request_id: str,
    payload: FeatureRequestUpdate,
    current_user: dict = Depends(require_roles("admin")),
):
    db = get_database()
    now = datetime.now(timezone.utc).isoformat()
    update = {"status": payload.status, "admin_note": payload.admin_note.strip() if payload.admin_note else None, "updated_at": now}
    result = await db.feature_requests.update_one({"_id": request_id}, {"$set": update})
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Feature request not found")
    doc = await db.feature_requests.find_one({"_id": request_id})
    await record_audit_log(
        action="FEATURE_REQUEST_UPDATED",
        resource_type="feature_request",
        resource_id=request_id,
        actor=current_user,
        details={"status": payload.status},
    )
    return _serialize(doc, include_admin_note=True)
