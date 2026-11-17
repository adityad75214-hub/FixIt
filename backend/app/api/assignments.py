from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.security import get_current_user, require_roles
from app.core.audit import record_audit_log
from app.models.ticket import TicketAssign, TicketStatus
from app.services.assignment_service import get_staff_workload, find_best_staff_for_ticket
from app.services.notification_service import send_notification

router = APIRouter(prefix="/assignments", tags=["Staff Assignment"])

@router.get("/workload", response_model=List[Dict[str, Any]])
async def get_workload_metrics(current_user: dict = Depends(require_roles("admin", "staff"))):
    workload = await get_staff_workload()
    if current_user["role"] == "staff":
        return [item for item in workload if item.get("staff_id") == current_user["id"]]
    return workload

@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assignment: TicketAssign,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    ticket = await db.tickets.find_one({"$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if ticket.get("status") in {TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value}:
        raise HTTPException(status_code=409, detail="Resolved or closed tickets cannot be assigned. Reopen the ticket first.")

    staff_user = await db.users.find_one({"_id": assignment.staff_id, "role": "staff", "is_active": True})
    if not staff_user:
        raise HTTPException(status_code=404, detail="IT Staff member not found or inactive")

    now_iso = datetime.now(timezone.utc).isoformat()
    old_assigned = ticket.get("assigned_to")
    action_name = "REASSIGNED" if old_assigned else "ASSIGNED"

    assigned_staff_data = {
        "id": str(staff_user["_id"]),
        "name": staff_user["name"],
        "email": staff_user["email"],
        "role": staff_user["role"],
        "specialization": staff_user.get("specialization") or []
    }

    timeline_event = {
        "action": f"TICKET_{action_name}",
        "actor_name": current_user["name"],
        "actor_role": current_user["role"],
        "actor_id": current_user["id"],
        "timestamp": now_iso,
        "note": assignment.note or f"Assigned to {staff_user['name']} by {current_user['name']}",
        "old_value": old_assigned.get("name") if old_assigned else "Unassigned",
        "new_value": staff_user["name"]
    }

    new_status = TicketStatus.ASSIGNED.value if ticket.get("status") == TicketStatus.OPEN.value else ticket.get("status")

    update_result = await db.tickets.update_one(
        {"_id": ticket["_id"], "updated_at": ticket.get("updated_at")},
        {
            "$set": {
                "assigned_to": assigned_staff_data,
                "status": new_status,
                "updated_at": now_iso
            },
            "$push": {"timeline": timeline_event}
        }
    )
    if not update_result.matched_count:
        raise HTTPException(status_code=409, detail="This ticket changed while you were assigning it. Refresh and try again.")

    # Notify staff
    await send_notification(
        user_id=str(staff_user["_id"]),
        title=f"Ticket Assigned: {ticket['ticket_id']}",
        message=f"You have been assigned ticket: '{ticket['title']}' ({ticket['category']})",
        link=f"/tickets/{ticket['_id']}",
        notif_type="ticket_assigned"
    )

    await record_audit_log(
        action=f"TICKET_{action_name}",
        resource_type="ticket",
        resource_id=ticket["ticket_id"],
        actor=current_user,
        details={"assigned_to": staff_user["name"], "staff_id": str(staff_user["_id"])}
    )

    return {
        "message": f"Ticket successfully {action_name.lower()} to {staff_user['name']}",
        "assigned_to": assigned_staff_data
    }

@router.post("/{ticket_id}/auto-assign")
async def trigger_auto_assign(
    ticket_id: str,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    ticket = await db.tickets.find_one({"$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    staff = await find_best_staff_for_ticket(ticket.get("category", ""))
    if not staff:
        raise HTTPException(status_code=400, detail="No available IT staff members found for automatic assignment")

    assignment = TicketAssign(staff_id=staff["id"], note="Automatic assignment via workload balancing")
    return await assign_ticket(ticket_id, assignment, current_user)
