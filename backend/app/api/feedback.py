import uuid
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_database
from app.core.security import get_current_user, require_roles
from app.core.audit import record_audit_log
from app.models.feedback import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["Feedback & Ratings"])

@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback_in: FeedbackCreate,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    ticket = await db.tickets.find_one({
        "$or": [{"_id": feedback_in.ticket_id}, {"ticket_id": feedback_in.ticket_id}]
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Only ticket creator can submit feedback
    if ticket.get("created_by", {}).get("id") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the user who reported this issue can provide feedback.")

    # Ticket must be resolved or closed
    if ticket.get("status") not in ["resolved", "closed"]:
        raise HTTPException(status_code=400, detail="Feedback can only be submitted after ticket resolution.")

    # Prevent duplicate feedback
    existing = await db.feedback.find_one({"ticket_id": ticket["ticket_id"]})
    if existing:
        raise HTTPException(status_code=400, detail="Feedback has already been submitted for this ticket.")

    feedback_id = f"FDB-{uuid.uuid4().hex[:8].upper()}"
    now_iso = datetime.now(timezone.utc).isoformat()

    doc = {
        "_id": feedback_id,
        "ticket_id": ticket["ticket_id"],
        "ticket_custom_id": ticket["ticket_id"],
        "ticket_db_id": str(ticket["_id"]),
        "rating": feedback_in.rating,
        "comments": feedback_in.comments,
        "created_by": {
            "id": current_user["id"],
            "name": current_user["name"],
            "email": current_user["email"],
            "role": current_user["role"]
        },
        "created_at": now_iso
    }

    try:
        await db.feedback.insert_one(doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="Feedback has already been submitted for this ticket.") from None
    await db.tickets.update_one({"_id": ticket["_id"]}, {"$set": {"has_feedback": True}})

    await record_audit_log(
        action="FEEDBACK_SUBMITTED",
        resource_type="feedback",
        resource_id=feedback_id,
        actor=current_user,
        details={"ticket_id": ticket["ticket_id"], "rating": feedback_in.rating}
    )

    return FeedbackResponse(
        id=feedback_id,
        ticket_id=ticket["ticket_id"],
        ticket_custom_id=ticket["ticket_id"],
        rating=feedback_in.rating,
        comments=feedback_in.comments,
        created_by=doc["created_by"],
        created_at=now_iso
    )

@router.get("/metrics")
async def get_feedback_metrics(current_user: dict = Depends(require_roles("admin"))):
    db = get_database()
    # Aggregate every review rather than silently truncating at the previous 1,000-row cap.
    summary = await db.feedback.aggregate([
        {"$group": {
            "_id": None,
            "total_reviews": {"$sum": 1},
            "average_rating": {"$avg": "$rating"},
        }}
    ]).to_list(1)

    distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    rating_counts = await db.feedback.aggregate([
        {"$group": {"_id": "$rating", "count": {"$sum": 1}}}
    ]).to_list(5)
    for row in rating_counts:
        rating = row.get("_id")
        if rating in distribution:
            distribution[rating] = row.get("count", 0)

    recent_docs = await db.feedback.find().sort("created_at", -1).limit(10).to_list(10)
    recent = [
        {
            "id": str(item["_id"]),
            "ticket_id": item["ticket_id"],
            "rating": item["rating"],
            "comments": item.get("comments"),
            "author_name": (item.get("created_by") or {}).get("name", "Unknown"),
            "created_at": item.get("created_at", ""),
        }
        for item in recent_docs
    ]

    total = summary[0].get("total_reviews", 0) if summary else 0
    average = summary[0].get("average_rating") if summary else None
    return {
        "total_reviews": total,
        "average_rating": round(float(average), 2) if average is not None else 0.0,
        "distribution": distribution,
        "recent_reviews": recent,
    }
