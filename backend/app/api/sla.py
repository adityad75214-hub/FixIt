from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_database
from app.core.security import require_roles, get_current_user
from app.core.audit import record_audit_log
from app.models.sla import SLAPolicyResponse, SLAPolicyCreate
from app.services.sla_service import check_ticket_sla

router = APIRouter(prefix="/sla", tags=["SLA Policies"])

@router.get("/policies", response_model=List[SLAPolicyResponse])
async def get_sla_policies(current_user: dict = Depends(get_current_user)):
    db = get_database()
    policies = await db.sla_policies.find().to_list(10)
    return [
        SLAPolicyResponse(
            id=str(p["_id"]),
            priority=p["priority"],
            target_resolution_hours=p["target_resolution_hours"],
            target_response_hours=p["target_response_hours"],
            description=p.get("description", ""),
            updated_at=p.get("updated_at", "")
        )
        for p in policies
    ]

@router.put("/policies/{priority}", response_model=SLAPolicyResponse)
async def update_sla_policy(
    priority: str,
    policy_in: SLAPolicyCreate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    now_iso = datetime.now(timezone.utc).isoformat()

    await db.sla_policies.update_one(
        {"priority": priority.lower()},
        {
            "$set": {
                "target_resolution_hours": policy_in.target_resolution_hours,
                "target_response_hours": policy_in.target_response_hours,
                "description": policy_in.description,
                "updated_at": now_iso
            }
        },
        upsert=True
    )

    await record_audit_log(
        action="SLA_POLICY_UPDATED",
        resource_type="sla_policy",
        resource_id=priority,
        actor=current_user,
        details={
            "priority": priority,
            "target_resolution_hours": policy_in.target_resolution_hours,
            "target_response_hours": policy_in.target_response_hours
        }
    )

    updated = await db.sla_policies.find_one({"priority": priority.lower()})
    return SLAPolicyResponse(
        id=str(updated["_id"]),
        priority=updated["priority"],
        target_resolution_hours=updated["target_resolution_hours"],
        target_response_hours=updated["target_response_hours"],
        description=updated.get("description", ""),
        updated_at=updated.get("updated_at", now_iso)
    )

@router.get("/overdue-tickets")
async def get_overdue_tickets(current_user: dict = Depends(require_roles("admin", "staff"))):
    db = get_database()
    # Find all active tickets
    active_query = {"status": {"$in": ["open", "assigned", "in_progress", "on_hold", "reopened"]}}
    if current_user["role"] == "staff":
        active_query["$or"] = [
            {"assigned_to.id": current_user["id"]},
            {"assigned_to": None},
            {"assigned_to": {"$exists": False}},
        ]
    overdue_list = []
    async for t in db.tickets.find(active_query):
        is_overdue, remaining = check_ticket_sla(t)
        if is_overdue:
            overdue_list.append({
                "id": str(t["_id"]),
                "ticket_id": t["ticket_id"],
                "title": t["title"],
                "priority": t["priority"],
                "category": t["category"],
                "building": t["building"],
                "room": t["room"],
                "assigned_to": t.get("assigned_to"),
                "created_at": t["created_at"],
                "sla_deadline": t.get("sla_deadline"),
                "overdue_by_minutes": abs(remaining)
            })

    return {"overdue_count": len(overdue_list), "tickets": overdue_list}
