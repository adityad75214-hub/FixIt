import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Literal, Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from app.core.database import get_database
from app.core.security import require_roles
from app.core.audit import record_audit_log
from app.core.tenancy import institution_id_for, scoped_filter

router = APIRouter(prefix="/incidents", tags=["Master Incidents"])

class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    description: str = Field(..., min_length=10, max_length=3000)
    category: str = Field(..., min_length=2, max_length=80)
    building: Optional[str] = Field(default=None, max_length=100)
    severity: Literal["critical", "high", "medium", "low"] = "high"
    linked_ticket_ids: List[Annotated[str, Field(max_length=100)]] = Field(default_factory=list, max_length=100)

    @field_validator("title", "description", "category")
    @classmethod
    def reject_blank_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("This field cannot be blank.")
        return cleaned


class IncidentStatusUpdate(BaseModel):
    status: Literal["investigating", "identified", "monitoring", "resolved"]

@router.get("", response_model=List[Dict[str, Any]])
async def list_incidents(current_user: dict = Depends(require_roles("admin", "staff"))):
    db = get_database()
    incidents = await db.incidents.find({"institution_id": institution_id_for(current_user)}).sort("created_at", -1).to_list(None)
    return [
        {
            "id": str(incident.get("_id", "")),
            "title": incident.get("title"),
            "description": incident.get("description"),
            "category": incident.get("category"),
            "building": incident.get("building"),
            "severity": incident.get("severity"),
            "status": incident.get("status"),
            "linked_ticket_count": len(incident.get("linked_ticket_ids") or []),
            "created_at": incident.get("created_at"),
            "updated_at": incident.get("updated_at"),
        }
        for incident in incidents
    ]

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_incident(
    incident_in: IncidentCreate,
    current_user: dict = Depends(require_roles("admin", "staff"))
):
    db = get_database()
    requested_ids = list(dict.fromkeys(incident_in.linked_ticket_ids))
    matched_tickets = []
    if requested_ids:
        ticket_query: Dict[str, Any] = {
            "$or": [
                {"_id": {"$in": requested_ids}},
                {"ticket_id": {"$in": requested_ids}},
            ]
        }
        ticket_query["institution_id"] = institution_id_for(current_user)
        if current_user["role"] == "staff":
            ticket_query["assigned_to.id"] = current_user["id"]
        matched_tickets = await db.tickets.find(ticket_query).to_list(len(requested_ids))
        found_ids = set()
        for ticket in matched_tickets:
            found_ids.add(str(ticket.get("_id")))
            found_ids.add(str(ticket.get("ticket_id")))
        if any(ticket_id not in found_ids for ticket_id in requested_ids):
            raise HTTPException(
                status_code=403 if current_user["role"] == "staff" else 404,
                detail="One or more selected tickets do not exist or are not available to you.",
            )
        if any(ticket.get("linked_incident_id") for ticket in matched_tickets):
            raise HTTPException(status_code=409, detail="A selected ticket is already linked to another incident.")

    now_iso = datetime.now(timezone.utc).isoformat()
    inc_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    matched_custom_ids = [ticket["ticket_id"] for ticket in matched_tickets]
    doc = {
        "_id": inc_id,
        "institution_id": institution_id_for(current_user),
        "title": incident_in.title,
        "description": incident_in.description,
        "category": incident_in.category,
        "building": incident_in.building,
        "severity": incident_in.severity,
        "status": "investigating",
        "created_by": {"id": current_user["id"], "name": current_user["name"]},
        "linked_ticket_ids": matched_custom_ids,
        "created_at": now_iso,
        "updated_at": now_iso,
    }
    await db.incidents.insert_one(doc)

    if matched_custom_ids:
        link_result = await db.tickets.update_many(
            {"ticket_id": {"$in": matched_custom_ids}, "institution_id": institution_id_for(current_user), "linked_incident_id": None},
            {"$set": {"linked_incident_id": inc_id}},
        )
        if link_result.matched_count != len(matched_custom_ids):
            # Roll back our partial writes if a concurrent request linked a ticket first.
            await db.tickets.update_many(
                {"linked_incident_id": inc_id, "institution_id": institution_id_for(current_user)},
                {"$unset": {"linked_incident_id": ""}},
            )
            await db.incidents.delete_one({"_id": inc_id, "institution_id": institution_id_for(current_user)})
            raise HTTPException(status_code=409, detail="A selected ticket was linked to another incident. Refresh and retry.")

    await record_audit_log(
        action="INCIDENT_CREATED",
        resource_type="incident",
        resource_id=inc_id,
        actor=current_user,
        details={"title": incident_in.title, "linked_count": len(matched_custom_ids)},
    )
    return {
        "id": inc_id,
        "title": doc["title"],
        "description": doc["description"],
        "category": doc["category"],
        "building": doc["building"],
        "severity": doc["severity"],
        "status": doc["status"],
        "linked_ticket_count": len(matched_custom_ids),
        "created_at": now_iso,
        "updated_at": now_iso,
    }


@router.patch("/{incident_id}")
async def update_incident_status(
    incident_id: str,
    payload: IncidentStatusUpdate,
    current_user: dict = Depends(require_roles("admin")),
):
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()
    result = await db.incidents.update_one(
        {"_id": incident_id, "institution_id": institution_id_for(current_user)},
        {"$set": {"status": payload.status, "updated_at": now_iso}},
    )
    if not result.matched_count:
        raise HTTPException(status_code=404, detail="Incident not found")
    await record_audit_log(
        action="INCIDENT_STATUS_UPDATED",
        resource_type="incident",
        resource_id=incident_id,
        actor=current_user,
        details={"status": payload.status},
    )
    incident = await db.incidents.find_one({"_id": incident_id, "institution_id": institution_id_for(current_user)})
    return {
        "id": incident_id,
        "title": incident.get("title"),
        "description": incident.get("description"),
        "category": incident.get("category"),
        "building": incident.get("building"),
        "severity": incident.get("severity"),
        "status": incident.get("status"),
        "linked_ticket_count": len(incident.get("linked_ticket_ids") or []),
        "created_at": incident.get("created_at"),
        "updated_at": incident.get("updated_at"),
    }

