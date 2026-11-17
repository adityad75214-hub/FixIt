import asyncio
import smtplib
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from typing import Optional

from app.core.config import settings
from app.core.database import get_database


def _send_email(recipient: str, subject: str, body: str) -> None:
    """Send an email only when SMTP is explicitly configured."""
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or ""
    message["To"] = recipient
    message.set_content(body)

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
        if settings.SMTP_STARTTLS:
            server.starttls()
        if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.send_message(message)


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

        user = await db.users.find_one({"_id": user_id})
        if not user:
            return
        institution_id = user.get("institution_id") or "INST-DEFAULT"
        preferences = await db.user_preferences.find_one({"user_id": user_id, "institution_id": institution_id}) or {}
        now = datetime.now(timezone.utc).isoformat()

        if preferences.get("in_app_notifications", True):
            notif = {
                "_id": f"NOTIF-{uuid.uuid4().hex[:12].upper()}",
                "user_id": user_id,
                "institution_id": institution_id,
                "title": title,
                "message": message,
                "link": link,
                "type": notif_type,
                "is_read": False,
                "created_at": now
            }
            await db.notifications.insert_one(notif)

        # Email is opt-in by preference and remains disabled until SMTP is configured.
        if (
            preferences.get("email_notifications", True)
            and user
            and user.get("email")
            and settings.SMTP_HOST
            and (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME)
        ):
            body = message
            if link:
                body += f"\n\nOpen FixIt: {settings.APP_BASE_URL.rstrip('/') + link if settings.APP_BASE_URL and link.startswith('/') else link}"
            try:
                await asyncio.to_thread(_send_email, user["email"], title, body)
            except Exception as email_error:
                print(f"Warning: FixIt email notification failed: {email_error}")
    except Exception as e:
        print(f"Warning: Failed to create notification: {e}")


async def notify_admins(title: str, message: str, link: Optional[str] = None, notif_type: str = "admin_alert", institution_id: Optional[str] = None):
    try:
        db = get_database()
        query = {"role": "admin", "is_active": True}
        if institution_id:
            query["institution_id"] = institution_id
        admins = await db.users.find(query).to_list(20)
        for admin in admins:
            await send_notification(str(admin["_id"]), title, message, link, notif_type)
    except Exception as e:
        print(f"Warning: Failed to notify admins: {e}")
