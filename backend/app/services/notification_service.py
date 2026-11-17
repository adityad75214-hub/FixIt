import uuid
from datetime import datetime, timezone
from typing import Optional, List
from app.core.database import get_database

async def send_notification(
    user_id: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    notif_type: str = "ticket_update"
):
    try:
        db = get_database()
        if db is None:
            return

        notif = {
            "_id": f"NOTIF-{uuid.uuid4().hex[:12].upper()}",
            "user_id": user_id,
            "title": title,
            "message": message,
            "link": link,
            "type": notif_type,
            "is_read": False,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.notifications.insert_one(notif)
    except Exception as e:
        print(f"Warning: Failed to create notification: {e}")

async def notify_admins(title: str, message: str, link: Optional[str] = None, notif_type: str = "admin_alert"):
    try:
        db = get_database()
        admins = await db.users.find({"role": "admin", "is_active": True}).to_list(20)
        for admin in admins:
            await send_notification(str(admin["_id"]), title, message, link, notif_type)
    except Exception as e:
        print(f"Warning: Failed to notify admins: {e}")
