import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from app.core.database import get_database
from app.core.security import get_current_user, require_roles
from app.core.audit import record_audit_log
from app.core.tenancy import institution_id_for, scoped_filter
from app.models.ticket import (
    TicketCreate,
    TicketResponse,
    TicketStatusUpdate,
    TicketPriorityUpdate,
    TicketPriority,
    TicketStatus
)
from app.services.ticket_service import (
    generate_ticket_id,
    detect_potential_duplicates,
    calculate_sla_deadline_from_db,
    validate_status_transition,
    validate_campus_location,
    suggest_priority
)
from app.services.sla_service import check_ticket_sla
from app.services.assignment_service import find_best_staff_for_ticket
from app.services.notification_service import send_notification, notify_admins

router = APIRouter(prefix="/tickets", tags=["Tickets"])


class DuplicateCheckRequest(BaseModel):
    title: str = Field(default="", max_length=150)
    category: str = Field(default="", max_length=80)
    building: str = Field(default="", max_length=100)
    room: str = Field(default="", max_length=100)
    campus_id: Optional[str] = Field(default=None, max_length=80)


class TicketIncidentLinkRequest(BaseModel):
    incident_id: str = Field(..., min_length=1, max_length=100)

def format_ticket_doc(doc: Dict[str, Any]) -> TicketResponse:
    is_overdue, remaining_mins = check_ticket_sla(doc)
    doc_id = str(doc.get("_id"))
    return TicketResponse(
        id=doc_id,
        ticket_id=doc.get("ticket_id", doc_id),
        title=doc.get("title", ""),
        description=doc.get("description", ""),
        category=doc.get("category", ""),
        problem_domain=doc.get("problem_domain", "technical"),
        location_type=doc.get("location_type", "campus"),
        subcategory=doc.get("subcategory"),
        priority=doc.get("priority", TicketPriority.MEDIUM),
        status=doc.get("status", TicketStatus.OPEN),
        campus_id=doc.get("campus_id"),
        building=doc.get("building", ""),
        floor=doc.get("floor"),
        room=doc.get("room", ""),
        department=doc.get("department"),
        affected_users=doc.get("affected_users", 1),
        attachments=doc.get("attachments", []),
        created_by=doc.get("created_by", {}),
        assigned_to=doc.get("assigned_to"),
        created_at=doc.get("created_at", ""),
        updated_at=doc.get("updated_at", ""),
        sla_deadline=doc.get("sla_deadline"),
        sla_target_hours=doc.get("sla_target_hours", 24),
        is_overdue=is_overdue,
        time_remaining_minutes=remaining_mins,
        first_response_at=doc.get("first_response_at"),
        resolved_at=doc.get("resolved_at"),
        closed_at=doc.get("closed_at"),
        resolution_notes=doc.get("resolution_notes"),
        hold_reason=doc.get("hold_reason"),
        timeline=doc.get("timeline", []),
        has_feedback=doc.get("has_feedback", False),
        linked_incident_id=doc.get("linked_incident_id")
    )

@router.post("/check-duplicates")
async def check_duplicates(payload: DuplicateCheckRequest, current_user: dict = Depends(get_current_user)):
    title = payload.title
    category = payload.category
    building = payload.building
    room = payload.room
    campus_id = payload.campus_id
    duplicates = await detect_potential_duplicates(title, category, building, room, campus_id=campus_id, institution_id=institution_id_for(current_user))
    role = current_user["role"]
    if role in ("student", "faculty"):
        visible = [item for item in duplicates if item.get("_created_by_id") == current_user["id"]]
    elif role == "staff":
        visible = [item for item in duplicates if item.get("_assigned_to_id") in (None, current_user["id"])]
    else:
        visible = duplicates

    has_restricted_matches = len(visible) < len(duplicates)
    safe_duplicates = [
        {key: value for key, value in item.items() if not key.startswith("_")}
        for item in visible
    ]
    return {
        "potential_duplicates": safe_duplicates,
        "count": len(safe_duplicates),
        "has_restricted_matches": has_restricted_matches,
    }

@router.post("", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_in: TicketCreate,
    auto_assign: bool = Query(True, description="Attempt automatic staff assignment"),
    current_user: dict = Depends(get_current_user)
):
    db = get_database()

    # Campus issues use the configured hierarchy; remote and location-independent
    # requests share the same ticket lifecycle without requiring campus coordinates.
    derived_dept = None
    if ticket_in.location_type == "campus":
        is_valid_loc, loc_error, derived_dept = await validate_campus_location(
            ticket_in.building,
            ticket_in.floor or "Ground",
            ticket_in.room,
            campus_id=ticket_in.campus_id,
            institution_id=institution_id_for(current_user),
        )
        if not is_valid_loc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=loc_error or "Invalid campus location combination provided."
            )
    else:
        ticket_in.campus_id = None
        ticket_in.building = "Not applicable"
        ticket_in.floor = "Not applicable"
        ticket_in.room = "Not applicable"

    ticket_custom_id = await generate_ticket_id()
    doc_id = f"TCK-{uuid.uuid4().hex[:10].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Determine priority
    priority = ticket_in.priority or suggest_priority(
        ticket_in.category,
        ticket_in.affected_users or 1,
        is_classroom="classroom" in ticket_in.room.lower()
    )

    # Calculate SLA target & deadline from database policy
    sla_deadline, target_hours = await calculate_sla_deadline_from_db(priority.value)

    # Initial timeline event
    initial_timeline = [{
        "action": "TICKET_CREATED",
        "actor_name": current_user["name"],
        "actor_role": current_user["role"],
        "actor_id": current_user["id"],
        "timestamp": now_iso,
        "note": f"Ticket submitted by {current_user['name']} ({current_user['role']})"
    }]

    creator_info = {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"],
        "department": current_user.get("department") or ticket_in.department,
        "phone": current_user.get("phone")
    }

    initial_status = TicketStatus.OPEN.value
    assigned_staff = None

    # Check auto assignment
    if auto_assign:
        staff = await find_best_staff_for_ticket(ticket_in.category, institution_id_for(current_user))
        if staff:
            assigned_staff = staff
            initial_status = TicketStatus.ASSIGNED.value
            initial_timeline.append({
                "action": "AUTO_ASSIGNED",
                "actor_name": "System",
                "actor_role": "system",
                "actor_id": "system",
                "timestamp": now_iso,
                "note": f"Auto-assigned to IT staff {staff['name']} based on specialization/workload"
            })

    ticket_doc = {
        "_id": doc_id,
        "ticket_id": ticket_custom_id,
        "title": ticket_in.title,
        "description": ticket_in.description,
        "category": ticket_in.category,
        "problem_domain": ticket_in.problem_domain,
        "location_type": ticket_in.location_type,
        "subcategory": ticket_in.subcategory,
        "priority": priority.value,
        "status": initial_status,
        "campus_id": ticket_in.campus_id,
        "institution_id": institution_id_for(current_user),
        "building": ticket_in.building,
        "floor": ticket_in.floor,
        "room": ticket_in.room,
        "department": ticket_in.department or current_user.get("department"),
        "affected_users": ticket_in.affected_users or 1,
        "attachments": ticket_in.attachments or [],
        "created_by": creator_info,
        "assigned_to": assigned_staff,
        "created_at": now_iso,
        "updated_at": now_iso,
        "sla_deadline": sla_deadline.isoformat(),
        "sla_target_hours": target_hours,
        "timeline": initial_timeline,
        "has_feedback": False,
        "linked_incident_id": None
    }

    await db.tickets.insert_one(ticket_doc)

    # In-app notifications
    if assigned_staff:
        await send_notification(
            user_id=assigned_staff["id"],
            title=f"New Ticket Assigned: {ticket_custom_id}",
            message=f"{ticket_in.title} in {ticket_in.building} Room {ticket_in.room}",
            link=f"/tickets/{doc_id}",
            notif_type="ticket_assigned"
        )
    await notify_admins(
        title=f"New Ticket Created: {ticket_custom_id}",
        message=f"[{priority.value.upper()}] {ticket_in.title} ({ticket_in.category})",
        link=f"/tickets/{doc_id}",
        notif_type="ticket_created"
    )

    await record_audit_log(
        action="TICKET_CREATED",
        resource_type="ticket",
        resource_id=ticket_custom_id,
        actor=current_user,
        details={"title": ticket_in.title, "priority": priority.value, "category": ticket_in.category}
    )

    return format_ticket_doc(ticket_doc)

@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    ticket_status: Optional[str] = Query(default=None, alias="status", max_length=30),
    priority: Optional[str] = Query(default=None, max_length=20),
    category: Optional[str] = Query(default=None, max_length=80),
    problem_domain: Optional[str] = Query(default=None, max_length=40),
    building: Optional[str] = Query(default=None, max_length=100),
    department: Optional[str] = Query(default=None, max_length=100),
    assigned_to_me: Optional[bool] = None,
    staff_id: Optional[str] = Query(default=None, max_length=100),
    search: Optional[str] = Query(default=None, max_length=100),
    sort_by: str = Query("newest", pattern="^(newest|oldest|priority_high|priority_low|overdue)$"),
    skip: int = Query(0, ge=0, le=100000),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    query = {"institution_id": institution_id_for(current_user)}
    user_role = current_user["role"]
    user_id = current_user["id"]

    # Role-based scoping:
    # Students & Faculty can ONLY view their own tickets
    if user_role in ("student", "faculty"):
        query["created_by.id"] = user_id
    elif user_role == "staff":
        if assigned_to_me:
            query["assigned_to.id"] = user_id
        else:
            # Staff may see their own workload and the unassigned queue, never another technician's tickets.
            query["$or"] = [
                {"assigned_to.id": user_id},
                {"assigned_to": None},
                {"assigned_to": {"$exists": False}},
            ]
    elif user_role != "admin":
        raise HTTPException(status_code=403, detail="Unsupported account role.")
    # Admin can view all tickets

    if staff_id:
        if user_role == "staff" and staff_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only filter by your own staff account.")
        query["assigned_to.id"] = staff_id
    if ticket_status:
        query["status"] = ticket_status
    if priority:
        query["priority"] = priority
    if category:
        query["category"] = category
    if problem_domain:
        allowed_domains = {"technical", "academic", "administrative", "facilities", "personal_support", "community", "other"}
        if problem_domain not in allowed_domains:
            raise HTTPException(status_code=400, detail="Unsupported problem domain filter.")
        query["problem_domain"] = problem_domain
    if building:
        query["building"] = building
    if department:
        query["department"] = department
    if search:
        search_clause = {"$or": [
            {"ticket_id": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"title": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"description": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"building": {"$regex": re.escape(search[:100]), "$options": "i"}},
            {"room": {"$regex": re.escape(search[:100]), "$options": "i"}}
        ]}
        if "$or" in query:
            scope_clause = {"$or": query.pop("$or")}
            query["$and"] = [scope_clause, search_clause]
        else:
            query.update(search_clause)

    # Priority labels are strings, so alphabetical sorting is not severity sorting.
    # Use an explicit rank to keep critical > high > medium > low in every page.
    if sort_by in ("priority_high", "priority_low"):
        ranks = {"critical": 1, "high": 2, "medium": 3, "low": 4}
        direction = 1 if sort_by == "priority_high" else -1
        pipeline = [
            {"$match": query},
            {"$addFields": {"_priority_rank": {"$switch": {
                "branches": [
                    {"case": {"$eq": ["$priority", priority]}, "then": rank}
                    for priority, rank in ranks.items()
                ],
                "default": 5,
            }}}},
            {"$sort": {"_priority_rank": direction, "created_at": -1}},
            {"$skip": skip},
            {"$limit": limit},
        ]
        docs = await db.tickets.aggregate(pipeline).to_list(limit)
    else:
        sort_order = [("created_at", -1)]
        if sort_by == "oldest":
            sort_order = [("created_at", 1)]
        elif sort_by == "overdue":
            sort_order = [("sla_deadline", 1)]
        cursor = db.tickets.find(query).sort(sort_order).skip(skip).limit(limit)
        docs = await cursor.to_list(limit)

    return [format_ticket_doc(doc) for doc in docs]

@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket_detail(ticket_id: str, current_user: dict = Depends(get_current_user)):
    db = get_database()
    ticket = await db.tickets.find_one(scoped_filter(current_user, {
        "$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]
    }))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # RBAC Privacy Rule: Students & Faculty must NEVER access other users' tickets
    if current_user["role"] in ("student", "faculty"):
        if ticket.get("created_by", {}).get("id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Access denied. You can only view your own tickets.")
    elif current_user["role"] == "staff":
        assigned_id = (ticket.get("assigned_to") or {}).get("id")
        if assigned_id not in (None, current_user["id"]):
            raise HTTPException(status_code=403, detail="Access denied. This ticket is assigned to another technician.")
    elif current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unsupported account role.")

    return format_ticket_doc(ticket)

@router.put("/{ticket_id}/status", response_model=TicketResponse)
async def update_ticket_status(
    ticket_id: str,
    status_update: TicketStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    ticket = await db.tickets.find_one({
        "$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Authorize user
    if current_user["role"] in ("student", "faculty"):
        if ticket.get("created_by", {}).get("id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="Unauthorized")
    elif current_user["role"] == "staff":
        if (ticket.get("assigned_to") or {}).get("id") != current_user["id"]:
            raise HTTPException(status_code=403, detail="You can only update tickets assigned to you.")
    elif current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Unsupported account role.")

    old_status = ticket.get("status")
    new_status = status_update.status.value

    # Validate lifecycle transition
    is_valid, reason = validate_status_transition(old_status, new_status, current_user["role"])
    if not is_valid:
        raise HTTPException(status_code=400, detail=reason)

    now_iso = datetime.now(timezone.utc).isoformat()
    update_fields = {
        "status": new_status,
        "updated_at": now_iso
    }

    if status_update.hold_reason:
        update_fields["hold_reason"] = status_update.hold_reason
    if status_update.resolution_notes:
        update_fields["resolution_notes"] = status_update.resolution_notes

    if new_status == TicketStatus.RESOLVED.value:
        update_fields["resolved_at"] = now_iso
    elif new_status == TicketStatus.CLOSED.value:
        update_fields["closed_at"] = now_iso

    # Append timeline event
    timeline_event = {
        "action": f"STATUS_CHANGED_TO_{new_status.upper()}",
        "actor_name": current_user["name"],
        "actor_role": current_user["role"],
        "actor_id": current_user["id"],
        "timestamp": now_iso,
        "note": status_update.note or status_update.resolution_notes or status_update.hold_reason or f"Status changed from {old_status} to {new_status}",
        "old_value": old_status,
        "new_value": new_status
    }

    update_result = await db.tickets.update_one(
        {"_id": ticket["_id"], "status": old_status, "updated_at": ticket.get("updated_at")},
        {
            "$set": update_fields,
            "$push": {"timeline": timeline_event}
        }
    )
    if not update_result.matched_count:
        raise HTTPException(status_code=409, detail="This ticket changed while you were updating it. Refresh and try again.")

    # Notify creator or staff
    creator_id = ticket.get("created_by", {}).get("id")
    if creator_id and creator_id != current_user["id"]:
        await send_notification(
            user_id=creator_id,
            title=f"Ticket {ticket['ticket_id']} Status Updated",
            message=f"Status is now: {new_status.replace('_', ' ').title()}",
            link=f"/tickets/{ticket['_id']}",
            notif_type="status_changed"
        )

    # Audit log
    await record_audit_log(
        action="TICKET_STATUS_CHANGED",
        resource_type="ticket",
        resource_id=ticket["ticket_id"],
        actor=current_user,
        details={"old_status": old_status, "new_status": new_status, "note": status_update.note}
    )

    updated_doc = await db.tickets.find_one(scoped_filter(current_user, {"_id": ticket["_id"]}))
    return format_ticket_doc(updated_doc)

@router.put("/{ticket_id}/priority", response_model=TicketResponse)
async def update_ticket_priority(
    ticket_id: str,
    priority_update: TicketPriorityUpdate,
    current_user: dict = Depends(require_roles("admin"))
):
    db = get_database()
    ticket = await db.tickets.find_one({
        "$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    old_priority = ticket.get("priority")
    new_priority = priority_update.priority.value
    now_iso = datetime.now(timezone.utc).isoformat()

    # Recalculate SLA deadline based on updated priority from active DB policy
    sla_deadline, target_hours = await calculate_sla_deadline_from_db(new_priority)

    timeline_event = {
        "action": "PRIORITY_OVERRIDE",
        "actor_name": current_user["name"],
        "actor_role": current_user["role"],
        "actor_id": current_user["id"],
        "timestamp": now_iso,
        "note": f"Priority adjusted to {new_priority.upper()}. Reason: {priority_update.reason or 'Administrative override'}",
        "old_value": old_priority,
        "new_value": new_priority
    }

    update_result = await db.tickets.update_one(
        {"_id": ticket["_id"], "priority": old_priority, "updated_at": ticket.get("updated_at")},
        {
            "$set": {
                "priority": new_priority,
                "sla_deadline": sla_deadline.isoformat(),
                "sla_target_hours": target_hours,
                "updated_at": now_iso
            },
            "$push": {"timeline": timeline_event}
        }
    )
    if not update_result.matched_count:
        raise HTTPException(status_code=409, detail="This ticket changed while you were updating its priority. Refresh and try again.")

    await record_audit_log(
        action="PRIORITY_OVERRIDE",
        resource_type="ticket",
        resource_id=ticket["ticket_id"],
        actor=current_user,
        details={"old_priority": old_priority, "new_priority": new_priority, "reason": priority_update.reason}
    )

    updated_doc = await db.tickets.find_one({"_id": ticket["_id"]})
    return format_ticket_doc(updated_doc)

@router.put("/{ticket_id}/link-incident")
async def link_ticket_to_incident(
    ticket_id: str,
    payload: TicketIncidentLinkRequest,
    current_user: dict = Depends(require_roles("admin", "staff"))
):
    incident_id = payload.incident_id.strip()

    db = get_database()
    ticket = await db.tickets.find_one(scoped_filter(current_user, {"$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]}))
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    if current_user["role"] == "staff" and (ticket.get("assigned_to") or {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="You can only link incidents to tickets assigned to you.")

    incident = await db.incidents.find_one(scoped_filter(current_user, {"_id": incident_id}))
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
    existing_incident_id = ticket.get("linked_incident_id")
    if existing_incident_id == incident_id:
        return {"message": f"Ticket is already linked to incident {incident_id}"}
    if existing_incident_id:
        raise HTTPException(status_code=409, detail="This ticket is already linked to another incident.")

    now_iso = datetime.now(timezone.utc).isoformat()
    update_result = await db.tickets.update_one(
        {"_id": ticket["_id"], "updated_at": ticket.get("updated_at"), "$or": [
            {"linked_incident_id": None}, {"linked_incident_id": {"$exists": False}}
        ]},
        {
            "$set": {"linked_incident_id": incident_id, "updated_at": now_iso},
            "$push": {
                "timeline": {
                    "action": "LINKED_TO_INCIDENT",
                    "actor_name": current_user["name"],
                    "actor_role": current_user["role"],
                    "actor_id": current_user["id"],
                    "timestamp": now_iso,
                    "note": f"Linked to campus master incident {incident_id}"
                }
            }
        }
    )
    if not update_result.matched_count:
        raise HTTPException(status_code=409, detail="This ticket changed or was linked by another user. Refresh and try again.")

    await db.incidents.update_one(
        scoped_filter(current_user, {"_id": incident_id}),
        {"$addToSet": {"linked_ticket_ids": ticket["ticket_id"]}, "$set": {"updated_at": now_iso}}
    )
    await record_audit_log(
        action="TICKET_LINKED_TO_INCIDENT",
        resource_type="ticket",
        resource_id=ticket["ticket_id"],
        actor=current_user,
        details={"incident_id": incident_id},
    )
    return {"message": f"Ticket linked to incident {incident_id}"}

