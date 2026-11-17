from datetime import datetime, timezone
from typing import Dict, Any, Tuple

def check_ticket_sla(ticket: Dict[str, Any]) -> Tuple[bool, int]:
    """
    Returns (is_overdue, minutes_remaining).
    If already resolved/closed, is_overdue is based on whether resolved_at <= sla_deadline.
    """
    deadline_str = ticket.get("sla_deadline")
    if not deadline_str:
        return False, 999999

    try:
        deadline = datetime.fromisoformat(deadline_str.replace("Z", "+00:00"))
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        status = ticket.get("status")
        if status in ["resolved", "closed"]:
            resolved_at_str = ticket.get("resolved_at") or ticket.get("closed_at")
            if resolved_at_str:
                resolved_time = datetime.fromisoformat(resolved_at_str.replace("Z", "+00:00"))
                if resolved_time.tzinfo is None:
                    resolved_time = resolved_time.replace(tzinfo=timezone.utc)
                is_overdue = resolved_time > deadline
                return is_overdue, 0
            return False, 0

        diff = deadline - now
        minutes_remaining = int(diff.total_seconds() / 60)
        is_overdue = minutes_remaining < 0
        return is_overdue, minutes_remaining
    except (TypeError, ValueError, OverflowError):
        # A malformed deadline cannot be considered compliant; flag it for investigation.
        return True, 0
