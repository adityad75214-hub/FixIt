from typing import Optional
from pydantic import BaseModel

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    link: Optional[str] = None
    type: str = "ticket_update"  # ticket_created, ticket_assigned, status_changed, comment_added, sla_warning
    is_read: bool = False
    created_at: str
