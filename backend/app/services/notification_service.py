import asyncio
import logging
import smtplib
import ssl
import uuid
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import formataddr
from typing import Optional
from urllib.parse import urljoin

from app.core.config import settings
from app.core.database import get_database


logger = logging.getLogger(__name__)


def _send_email(recipient: str, subject: str, body: str) -> None:
    """Send one email using the configured SMTP server.

    Configuration and transport errors are deliberately raised to the caller so
    password-reset and verification flows can handle delivery failure safely.
    """
    host = (settings.SMTP_HOST or "").strip()
    sender = (settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME or "").strip()
    username = (settings.SMTP_USERNAME or "").strip()
    password = settings.SMTP_PASSWORD or ""

    if not host:
        raise RuntimeError("SMTP_HOST is not configured")
    if not sender:
        raise RuntimeError("SMTP_FROM_EMAIL or SMTP_USERNAME must be configured")
    if not recipient or not recipient.strip():
        raise ValueError("A recipient email address is required")
    if bool(username) != bool(password):
        raise RuntimeError("SMTP_USERNAME and SMTP_PASSWORD must be configured together")

    message = EmailMessage()
    message["Subject"] = subject
    sender_name = (settings.SMTP_FROM_NAME or "FixIt").strip() or "FixIt"
    message["From"] = formataddr((sender_name, sender))
    message["To"] = recipient.strip()
    message.set_content(body)

    timeout = 15
    if settings.SMTP_PORT == 465:
        # Port 465 uses implicit TLS; do not attempt STARTTLS on this port.
        with smtplib.SMTP_SSL(
            host,
            settings.SMTP_PORT,
            timeout=timeout,
            context=ssl.create_default_context(),
        ) as server:
            if username:
                server.login(username, password)
            server.send_message(message)
    elif settings.SMTP_STARTTLS:
        with smtplib.SMTP(host, settings.SMTP_PORT, timeout=timeout) as server:
            server.ehlo()
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
            if username:
                server.login(username, password)
            server.send_message(message)
    else:
        raise RuntimeError("SMTP transport must use STARTTLS or implicit TLS on port 465")


async def send_notification(
    user_id: str,
    title: str,
    message: str,
    link: Optional[str] = None,
    notif_type: str = "ticket_update",
):
    """Create an in-app notification and optionally deliver its email copy."""
    try:
        db = get_database()
        if db is None:
            logger.warning("Notification skipped because the database is unavailable")
            return

        user = await db.users.find_one({"_id": str(user_id)})
        if not user:
            return

        institution_id = str(user.get("institution_id") or "INST-DEFAULT")
        preferences = await db.user_preferences.find_one(
            {"user_id": str(user_id), "institution_id": institution_id}
        ) or {}
        now = datetime.now(timezone.utc).isoformat()

        if preferences.get("in_app_notifications", True):
            await db.notifications.insert_one({
                "_id": f"NOTIF-{uuid.uuid4().hex[:12].upper()}",
                "user_id": str(user_id),
                "institution_id": institution_id,
                "title": title,
                "message": message,
                "link": link,
                "type": notif_type,
                "is_read": False,
                "created_at": now,
            })

        email_enabled = (
            preferences.get("email_notifications", True)
            and bool(user.get("email"))
            and bool(settings.SMTP_HOST)
            and bool(settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME)
        )
        if email_enabled:
            body = message
            if link:
                base_url = (settings.APP_BASE_URL or "").strip()
                if link.startswith("/") and base_url:
                    body += f"\n\nOpen FixIt: {urljoin(base_url.rstrip('/') + '/', link.lstrip('/'))}"
                else:
                    body += f"\n\nOpen FixIt: {link}"
            try:
                await asyncio.to_thread(
                    _send_email, user["email"], title, body
                )
            except Exception:
                # Notification persistence must not fail because an email provider
                # is temporarily unavailable. The exception is logged, not hidden.
                logger.exception("FixIt email notification delivery failed")
    except Exception:
        logger.exception("Failed to create FixIt notification")


async def notify_admins(
    title: str,
    message: str,
    link: Optional[str] = None,
    notif_type: str = "admin_alert",
    institution_id: Optional[str] = None,
):
    """Notify active administrators, optionally within one institution."""
    try:
        db = get_database()
        if db is None:
            return

        query = {"role": "admin", "is_active": True}
        if institution_id:
            query["institution_id"] = institution_id

        admins = await db.users.find(query).to_list(20)
        for admin in admins:
            await send_notification(
                str(admin["_id"]), title, message, link, notif_type
            )
    except Exception:
        logger.exception("Failed to notify FixIt administrators")
