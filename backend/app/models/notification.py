from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    user_id: str
    title: str
    message: str
    link: Optional[str] = None
    type: str = Field(
        default="ticket_update",
        description="Notification event type, such as ticket_created or status_changed.",
    )
    is_read: bool = False
    created_at: str


class NotificationListResponse(BaseModel):
    unread_count: int = Field(default=0, ge=0)
    notifications: List[NotificationResponse] = Field(default_factory=list)
