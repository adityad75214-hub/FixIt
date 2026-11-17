import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.core.database import get_database

logger = logging.getLogger("fixit.audit")

async def record_audit_log(
    action: str,
    resource_type: str,
    resource_id: str,
    actor: Optional[Dict[str, Any]] = None,
    details: Optional[Dict[str, Any]] = None
):
    try:
        db = get_database()
        if db is None:
            return

        actor_info = {
            "user_id": actor.get("id") or str(actor.get("_id")) if actor else "system",
            "name": actor.get("name", "System") if actor else "System",
            "email": actor.get("email", "") if actor else "",
            "role": actor.get("role", "system") if actor else "system",
        }

        log_entry = {
            "_id": f"AUD-{uuid.uuid4().hex[:12].upper()}",
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "institution_id": (actor or {}).get("institution_id") or "INST-DEFAULT",
            "actor": actor_info,
            "details": details or {},
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await db.audit_logs.insert_one(log_entry)
    except Exception as exc:
        # Never expose request data or connection details through logs.
        logger.error("Audit log write failed (%s).", type(exc).__name__)
