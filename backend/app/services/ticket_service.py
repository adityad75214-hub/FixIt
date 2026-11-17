import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Tuple
from pymongo import ReturnDocument
from app.core.database import get_database
from app.core.config import settings
from app.models.ticket import TicketPriority, TicketStatus

async def generate_ticket_id() -> str:
    """Atomically increment and return the current year's ticket sequence."""
    db = get_database()
    current_year = datetime.now(timezone.utc).year
    counter_name = f"tickets_{current_year}"
    counter = await db.counters.find_one_and_update(
        {"name": counter_name},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    if not counter or not isinstance(counter.get("seq"), int):
        raise RuntimeError("Ticket sequence counter could not be allocated.")
    return f"FIXIT-{current_year}-{counter['seq']:04d}"

async def validate_campus_location(building: str, floor: str, room: str, campus_id: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate the complete configured hierarchy; never accept a mismatched partial hierarchy."""
    db = get_database()
    if not building or not floor or not room:
        return False, "Building, floor, and room are all required.", None
    if settings.is_production and not campus_id:
        return False, "Select a configured campus before submitting a ticket.", None

    # New campus hierarchy is authoritative whenever the building exists.
    building_query = {
        "name": {"$regex": f"^{re.escape(building.strip())}$", "$options": "i"},
        "is_active": True,
    }
    if campus_id:
        building_query["campus_id"] = campus_id
    b_doc = await db.buildings.find_one(building_query)
    if b_doc:
        b_id = str(b_doc["_id"])
        f_doc = await db.floors.find_one({
            "building_id": b_id,
            "floor_name": {"$regex": f"^{re.escape(floor.strip())}$", "$options": "i"},
            "is_active": True,
        })
        if not f_doc:
            configured_floors = await db.floors.count_documents({"building_id": b_id, "is_active": True})
            if not settings.is_production and configured_floors == 0:
                return True, None, None
            return False, f"Floor '{floor}' does not exist in building '{building}'. Ask an administrator to add it.", None

        f_id = str(f_doc["_id"])
        r_doc = await db.rooms.find_one({
            "floor_id": f_id,
            "building_id": b_id,
            "is_active": True,
            "$or": [
                {"room_number": {"$regex": f"^{re.escape(room.strip())}$", "$options": "i"}},
                {"room_name": {"$regex": f"^{re.escape(room.strip())}$", "$options": "i"}},
            ],
        })
        if not r_doc:
            # Administrator-defined places (hostel common rooms, washrooms, offices,
            # classrooms, gates inside a building, etc.) are valid ticket locations too.
            custom_location = await db.campus_locations.find_one({
                "location_type": "custom",
                "is_active": True,
                "building_id": b_id,
                "$or": [{"floor_id": f_id}, {"floor_id": None}, {"floor_id": {"$exists": False}}],
                "name": {"$regex": f"^{re.escape(room.strip())}$", "$options": "i"},
            })
            if custom_location:
                return True, None, None
            configured_rooms = await db.rooms.count_documents({"floor_id": f_id, "is_active": True})
            configured_custom = await db.campus_locations.count_documents({"building_id": b_id, "is_active": True, "location_type": "custom"})
            if not settings.is_production and configured_rooms == 0 and configured_custom == 0:
                return True, None, None
            return False, f"Location '{room}' is not configured for floor '{floor}' in building '{building}'. Ask an administrator to add it.", None
        return True, None, r_doc.get("department")

    # Legacy locations remain readable for existing installations during migration.
    loc_doc = await db.campus_locations.find_one({
        "building": {"$regex": f"^{re.escape(building.strip())}$", "$options": "i"},
        "is_active": True,
    })
    if loc_doc and not campus_id:
        floors = [str(value).casefold() for value in loc_doc.get("floors", [])]
        rooms = [str(value).casefold() for value in loc_doc.get("rooms", [])]
        if floor.strip().casefold() not in floors:
            return False, f"Floor '{floor}' is not valid for building '{building}'.", None
        if room.strip().casefold() not in rooms:
            return False, f"Room '{room}' is not valid for floor '{floor}' in building '{building}'.", None
        return True, None, None

    if not settings.is_production and not campus_id:
        # Development supports editable/manual values only when no campus was selected/configured.
        return True, None, None
    return False, f"Building '{building}' is not configured. Ask an administrator to add it before submitting a ticket.", None

def calculate_text_similarity(text1: str, text2: str) -> float:
    """Lightweight Jaccard token similarity for duplicate detection."""
    words1 = set(re.findall(r'\w+', text1.lower()))
    words2 = set(re.findall(r'\w+', text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    return len(intersection) / len(union)

async def detect_potential_duplicates(
    title: str,
    category: str,
    building: str,
    room: str,
    campus_id: Optional[str] = None,
    threshold: float = 0.35
) -> List[Dict[str, Any]]:
    db = get_database()
    query = {
        "status": {"$in": ["open", "assigned", "in_progress", "on_hold"]},
        "$or": [
            {"building": building},
            {"category": category}
        ]
    }
    if campus_id:
        query["campus_id"] = campus_id
    candidates = await db.tickets.find(query).limit(50).to_list(50)
    duplicates = []

    for ticket in candidates:
        sim = calculate_text_similarity(title, ticket.get("title", ""))
        same_loc = (ticket.get("building") == building and ticket.get("room", "").lower() == room.lower())
        same_cat = (ticket.get("category") == category)

        match_score = sim
        if same_cat and same_loc:
            match_score += 0.3
        elif same_cat:
            match_score += 0.15
        elif same_loc:
            match_score += 0.2

        if match_score >= threshold:
            duplicates.append({
                "ticket_id": ticket.get("ticket_id"),
                "id": str(ticket.get("_id")),
                "title": ticket.get("title"),
                "status": ticket.get("status"),
                "category": ticket.get("category"),
                "building": ticket.get("building"),
                "room": ticket.get("room"),
                "similarity_score": round(min(match_score, 1.0), 2),
                "created_at": ticket.get("created_at"),
                # Internal fields used by the API layer to enforce visibility before serialization.
                "_created_by_id": (ticket.get("created_by") or {}).get("id"),
                "_assigned_to_id": (ticket.get("assigned_to") or {}).get("id"),
            })

    duplicates.sort(key=lambda x: x["similarity_score"], reverse=True)
    return duplicates[:5]

def suggest_priority(category: str, affected_users: int = 1, is_classroom: bool = False) -> TicketPriority:
    critical_categories = ["Server and Infrastructure", "Projector and Smart Classroom"]
    if affected_users >= 50 or (category in critical_categories and affected_users >= 20):
        return TicketPriority.CRITICAL
    elif affected_users >= 10 or (is_classroom and category in critical_categories):
        return TicketPriority.HIGH
    elif category in ["Network and Wi-Fi", "Computer and Hardware"]:
        return TicketPriority.MEDIUM
    return TicketPriority.LOW

async def calculate_sla_deadline_from_db(priority: str) -> Tuple[datetime, int]:
    """Calculates SLA deadline using the active admin policy from the database."""
    db = get_database()
    policy = await db.sla_policies.find_one({"priority": priority.lower()})

    defaults = {
        TicketPriority.CRITICAL.value: 2,
        TicketPriority.HIGH.value: 8,
        TicketPriority.MEDIUM.value: 24,
        TicketPriority.LOW.value: 72
    }
    target_hours = policy.get("target_resolution_hours") if policy else defaults.get(priority.lower(), 24)
    deadline = datetime.now(timezone.utc) + timedelta(hours=target_hours)
    return deadline, target_hours

def validate_status_transition(current_status: str, new_status: str, user_role: str) -> Tuple[bool, str]:
    if current_status == new_status:
        return True, "No status change"

    if user_role == "admin":
        return True, "Admin override"

    if user_role in ("student", "faculty"):
        if current_status == TicketStatus.RESOLVED.value and new_status in (TicketStatus.CLOSED.value, TicketStatus.REOPENED.value):
            return True, "User confirmation or reopen"
        return False, f"Users can only close or reopen resolved tickets, not transition from {current_status} to {new_status}"

    allowed_staff_transitions = {
        TicketStatus.OPEN.value: [TicketStatus.ASSIGNED.value, TicketStatus.IN_PROGRESS.value],
        TicketStatus.ASSIGNED.value: [TicketStatus.IN_PROGRESS.value, TicketStatus.ON_HOLD.value],
        TicketStatus.IN_PROGRESS.value: [TicketStatus.ON_HOLD.value, TicketStatus.RESOLVED.value],
        TicketStatus.ON_HOLD.value: [TicketStatus.IN_PROGRESS.value, TicketStatus.RESOLVED.value],
        TicketStatus.RESOLVED.value: [TicketStatus.CLOSED.value, TicketStatus.REOPENED.value],
        TicketStatus.REOPENED.value: [TicketStatus.IN_PROGRESS.value, TicketStatus.RESOLVED.value],
        TicketStatus.CLOSED.value: [TicketStatus.REOPENED.value]
    }

    allowed = allowed_staff_transitions.get(current_status, [])
    if new_status in allowed:
        return True, "Valid transition"
    return False, f"Invalid status transition from {current_status} to {new_status}"
