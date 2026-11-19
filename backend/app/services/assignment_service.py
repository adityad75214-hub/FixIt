from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
from app.core.database import get_database
from app.core.audit import record_audit_log
from app.models.ticket import TicketStatus
from app.services.notification_service import notify_admins

async def get_staff_workload(institution_id: Optional[str] = None) -> List[Dict[str, Any]]:
    db = get_database()
    staff_query = {"role": "staff", "is_active": True}
    if institution_id:
        staff_query["institution_id"] = institution_id
    staff_members = await db.users.find(staff_query).to_list(None)

    workload_list = []
    for staff in staff_members:
        staff_id = str(staff["_id"])
        active_count = await db.tickets.count_documents({
            "assigned_to.id": staff_id,
            **({"institution_id": institution_id} if institution_id else {}),
            "status": {"$in": [TicketStatus.ASSIGNED.value, TicketStatus.IN_PROGRESS.value, TicketStatus.ON_HOLD.value, TicketStatus.REOPENED.value]}
        })
        resolved_count = await db.tickets.count_documents({
            "assigned_to.id": staff_id,
            **({"institution_id": institution_id} if institution_id else {}),
            "status": {"$in": [TicketStatus.RESOLVED.value, TicketStatus.CLOSED.value]}
        })

        workload_list.append({
            "staff_id": staff_id,
            "name": staff.get("name"),
            "email": staff.get("email"),
            "specialization": staff.get("specialization") or [],
            "active_tickets": active_count,
            "resolved_tickets": resolved_count,
            "is_active": staff.get("is_active", True)
        })

    return workload_list

async def find_best_staff_for_ticket(category: str, institution_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Automatic assignment with transparent scoring:
    Score = Specialization Match (40 pts) + Availability/Active Status (20 pts) + Workload Capacity (up to 40 pts).
    If no eligible staff is found, alerts administrators."""
    workload_list = await get_staff_workload(institution_id)
    if not workload_list:
        # Notify admins if no eligible staff
        await notify_admins(
            title="Auto-Assignment Alert: No Staff Available",
            message=f"Ticket created under category '{category}' could not be assigned. No active staff found.",
            notif_type="system_alert",
            institution_id=institution_id
        )
        return None

    def normalize(value: str) -> str:
        # Treat punctuation and spacing variants consistently, e.g.
        # "Network & Wi-Fi" and "Network and Wi-Fi".
        return "".join(character for character in (value or "").casefold() if character.isalnum())

    normalized_category = normalize(category)
    scored_candidates = []
    for staff in workload_list:
        if not staff.get("is_active", True):
            continue

        # A staff member is eligible only when at least one explicitly assigned
        # issue category matches. Workload must never override authorization/
        # capability by assigning an unrelated ticket.
        has_spec = any(
            normalize(spec) == normalized_category
            or (len(normalize(spec)) >= 4 and normalize(spec) in normalized_category)
            or (len(normalized_category) >= 4 and normalized_category in normalize(spec))
            for spec in staff.get("specialization", [])
            if isinstance(spec, str) and spec.strip()
        )
        if not has_spec:
            continue

        active_cnt = staff.get("active_tickets", 0)
        workload_score = max(0, 40 - (active_cnt * 5))
        avail_score = 20
        spec_score = 40
        total_score = spec_score + avail_score + workload_score
        scored_candidates.append({
            **staff,
            "score": total_score,
            "scoring_breakdown": {
                "specialization": spec_score,
                "availability": avail_score,
                "workload_capacity": workload_score,
                "total": total_score
            }
        })

    if not scored_candidates:
        await notify_admins(
            title="Auto-Assignment Alert: No Matching Staff",
            message=f"Ticket category '{category}' has no active staff member assigned to that issue category. The ticket remains unassigned.",
            notif_type="system_alert",
            institution_id=institution_id
        )
        return None

    # Among qualified staff, prefer the lowest active workload.
    scored_candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
    best = scored_candidates[0]

    db = get_database()
    staff_query = {"_id": best["staff_id"]}
    if institution_id:
        staff_query["institution_id"] = institution_id
    staff_user = await db.users.find_one(staff_query)
    if staff_user:
        return {
            "id": str(staff_user["_id"]),
            "name": staff_user["name"],
            "email": staff_user["email"],
            "role": staff_user["role"],
            "specialization": staff_user.get("specialization", []),
            "scoring_breakdown": best["scoring_breakdown"]
        }
    return None
