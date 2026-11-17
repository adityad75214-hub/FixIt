from typing import List, Dict, Any
from fastapi import APIRouter, Depends, status
from app.core.database import get_database
from app.core.security import get_current_user
from app.models.notification import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("", response_model=Dict[str, Any])
async def get_my_notifications(current_user: dict = Depends(get_current_user)):
    db = get_database()
    user_id = current_user["id"]

    docs = await db.notifications.find({"user_id": user_id}).sort("created_at", -1).limit(50).to_list(50)
    unread_count = await db.notifications.count_documents({"user_id": user_id, "is_read": False})

    notifs = [
        NotificationResponse(
            id=str(d["_id"]),
            user_id=d["user_id"],
            title=d["title"],
            message=d["message"],
            link=d.get("link"),
            type=d.get("type", "ticket_update"),
            is_read=d.get("is_read", False),
            created_at=d["created_at"]
        )
        for d in docs
    ]
    return {"unread_count": unread_count, "notifications": notifs}

@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    db = get_database()
    await db.notifications.update_one(
        {"_id": notification_id, "user_id": current_user["id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Notification marked as read"}

@router.put("/mark-all-read")
async def mark_all_notifications_as_read(current_user: dict = Depends(get_current_user)):
    db = get_database()
    await db.notifications.update_many(
        {"user_id": current_user["id"], "is_read": False},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}
