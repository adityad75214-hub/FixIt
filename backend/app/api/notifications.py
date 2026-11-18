from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.database import get_database
from app.core.security import get_current_user
from app.core.tenancy import institution_id_for
from app.models.notification import (
    NotificationListResponse,
    NotificationResponse,
)


router = APIRouter(prefix="/notifications", tags=["Notifications"])


def _serialize_notification(document: Dict[str, Any]) -> NotificationResponse:
    created_at = document.get("created_at", "")
    if isinstance(created_at, datetime):
        created_at = created_at.isoformat()
    elif created_at is None:
        created_at = ""

    return NotificationResponse(
        id=str(document["_id"]),
        user_id=str(document["user_id"]),
        title=str(document.get("title") or ""),
        message=str(document.get("message") or ""),
        link=document.get("link"),
        type=str(document.get("type") or "ticket_update"),
        is_read=bool(document.get("is_read", False)),
        created_at=str(created_at),
    )


@router.get("", response_model=NotificationListResponse)
async def get_my_notifications(
    current_user: dict = Depends(get_current_user),
) -> NotificationListResponse:
    db = get_database()
    user_id = str(current_user["id"])
    institution_id = institution_id_for(current_user)

    preferences = await db.user_preferences.find_one({
        "user_id": user_id,
        "institution_id": institution_id,
    }) or {}
    if not preferences.get("in_app_notifications", True):
        return NotificationListResponse()

    query = {
        "user_id": user_id,
        "institution_id": institution_id,
    }
    documents = await (
        db.notifications.find(query)
        .sort("created_at", -1)
        .limit(50)
        .to_list(length=50)
    )
    unread_count = await db.notifications.count_documents({
        **query,
        "is_read": False,
    })

    return NotificationListResponse(
        unread_count=unread_count,
        notifications=[_serialize_notification(document) for document in documents],
    )


@router.put("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    await db.notifications.update_one(
        {
            "_id": notification_id,
            "user_id": str(current_user["id"]),
            "institution_id": institution_id_for(current_user),
        },
        {"$set": {"is_read": True}},
    )
    # Keep the response generic so callers cannot probe another user's IDs.
    return {"message": "Notification marked as read"}


@router.put("/mark-all-read")
async def mark_all_notifications_as_read(
    current_user: dict = Depends(get_current_user),
):
    db = get_database()
    await db.notifications.update_many(
        {
            "user_id": str(current_user["id"]),
            "institution_id": institution_id_for(current_user),
            "is_read": False,
        },
        {"$set": {"is_read": True}},
    )
    return {"message": "All notifications marked as read"}
