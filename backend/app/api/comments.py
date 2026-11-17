import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.security import get_current_user
from app.core.audit import record_audit_log
from app.models.comment import CommentCreate, CommentResponse
from app.services.notification_service import send_notification

router = APIRouter(prefix="/comments", tags=["Comments & Notes"])

@router.get("/ticket/{ticket_id}", response_model=List[CommentResponse])
async def list_ticket_comments(
    ticket_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    ticket = await db.tickets.find_one({"$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    user_role = current_user["role"]
    # Students and faculty may only access conversations attached to their own tickets.
    if user_role in ("student", "faculty") and ticket.get("created_by", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only access comments on your own tickets.")
    if user_role == "staff" and (ticket.get("assigned_to") or {}).get("id") not in (None, current_user["id"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This ticket is assigned to another technician.")
    if user_role not in ("student", "faculty", "staff", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported account role.")

    query = {"ticket_id": ticket["ticket_id"]}

    # Students and Faculty MUST NEVER see internal notes
    if user_role in ("student", "faculty"):
        query["is_internal"] = False

    comments = await db.comments.find(query).sort("created_at", 1).to_list(None)
    return [
        CommentResponse(
            id=str(c["_id"]),
            ticket_id=c["ticket_id"],
            author=c["author"],
            content=c["content"],
            is_internal=c.get("is_internal", False),
            attachments=c.get("attachments", []),
            created_at=c["created_at"]
        )
        for c in comments
    ]

@router.post("/ticket/{ticket_id}", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    ticket_id: str,
    comment_in: CommentCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    ticket = await db.tickets.find_one({"$or": [{"_id": ticket_id}, {"ticket_id": ticket_id}]})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    user_role = current_user["role"]
    # Prevent authenticated users from commenting on tickets they do not own.
    if user_role in ("student", "faculty") and ticket.get("created_by", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only comment on your own tickets.")
    if user_role == "staff" and (ticket.get("assigned_to") or {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only comment on tickets assigned to you.")
    if user_role not in ("student", "faculty", "staff", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unsupported account role.")

    # Security check: Only staff and admin can post internal notes
    if comment_in.is_internal and user_role not in ("staff", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT staff and administrators can create internal notes."
        )

    now_iso = datetime.now(timezone.utc).isoformat()
    comment_id = f"CMT-{uuid.uuid4().hex[:10].upper()}"

    author_info = {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": user_role
    }

    doc = {
        "_id": comment_id,
        "ticket_id": ticket["ticket_id"],
        "ticket_db_id": str(ticket["_id"]),
        "author": author_info,
        "content": comment_in.content,
        "is_internal": comment_in.is_internal,
        "attachments": comment_in.attachments or [],
        "created_at": now_iso
    }

    await db.comments.insert_one(doc)

    # If first response from staff/admin, record first_response_at on ticket
    update_data = {"updated_at": now_iso}
    if user_role in ("staff", "admin") and not ticket.get("first_response_at") and not comment_in.is_internal:
        update_data["first_response_at"] = now_iso

    # Append timeline entry for public comments or note
    action_label = "INTERNAL_NOTE_ADDED" if comment_in.is_internal else "COMMENT_ADDED"
    await db.tickets.update_one(
        {"_id": ticket["_id"]},
        {
            "$set": update_data,
            "$push": {
                "timeline": {
                    "action": action_label,
                    "actor_name": current_user["name"],
                    "actor_role": user_role,
                    "actor_id": current_user["id"],
                    "timestamp": now_iso,
                    "note": f"{'Internal note' if comment_in.is_internal else 'Comment'}: {comment_in.content[:80]}..."
                }
            }
        }
    )

    # In-app notifications:
    # If staff commented publicly, notify creator
    creator_id = ticket.get("created_by", {}).get("id")
    assigned_staff_id = ticket.get("assigned_to", {}).get("id") if ticket.get("assigned_to") else None

    if not comment_in.is_internal:
        if user_role in ("staff", "admin") and creator_id and creator_id != current_user["id"]:
            await send_notification(
                user_id=creator_id,
                title=f"New Comment on {ticket['ticket_id']}",
                message=f"{current_user['name']} replied: {comment_in.content[:100]}",
                link=f"/tickets/{ticket['_id']}",
                notif_type="comment_added"
            )
        elif user_role in ("student", "faculty") and assigned_staff_id:
            await send_notification(
                user_id=assigned_staff_id,
                title=f"User Commented on {ticket['ticket_id']}",
                message=f"{current_user['name']} wrote: {comment_in.content[:100]}",
                link=f"/tickets/{ticket['_id']}",
                notif_type="comment_added"
            )

    return CommentResponse(
        id=comment_id,
        ticket_id=ticket["ticket_id"],
        author=author_info,
        content=comment_in.content,
        is_internal=comment_in.is_internal,
        attachments=comment_in.attachments or [],
        created_at=now_iso
    )
