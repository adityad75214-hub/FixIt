from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Annotated, Literal
from enum import Enum
from pydantic import BaseModel, Field

class TicketPriority(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TicketStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"

class TimelineEvent(BaseModel):
    action: str
    actor_name: str
    actor_role: str
    actor_id: str
    timestamp: str
    note: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None

class TicketCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    description: str = Field(..., min_length=10, max_length=5000)
    problem_domain: Literal["technical", "academic", "administrative", "facilities", "personal_support", "community", "other"] = "technical"
    location_type: Literal["campus", "remote", "not_applicable"] = "campus"
    category: str = Field(..., min_length=2, max_length=80)
    subcategory: Optional[str] = Field(default=None, max_length=80)
    priority: Optional[TicketPriority] = TicketPriority.MEDIUM
    campus_id: Optional[str] = None
    building: str = Field(default="Not specified", min_length=1, max_length=100)
    floor: Optional[str] = Field(default="Ground", max_length=50)
    room: str = Field(default="Not specified", min_length=1, max_length=100)
    department: Optional[str] = Field(default=None, max_length=100)
    affected_users: Optional[int] = Field(default=1, ge=1, le=10000)
    attachments: Optional[List[Annotated[str, Field(max_length=2048)]]] = Field(default_factory=list, max_length=5)

class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    note: Optional[str] = Field(default=None, max_length=1000)
    hold_reason: Optional[str] = Field(default=None, max_length=500)
    resolution_notes: Optional[str] = Field(default=None, max_length=5000)

class TicketPriorityUpdate(BaseModel):
    priority: TicketPriority
    reason: Optional[str] = Field(default=None, max_length=500)

class TicketAssign(BaseModel):
    staff_id: str = Field(..., min_length=1, max_length=100)
    note: Optional[str] = Field(default=None, max_length=500)

class TicketResponse(BaseModel):
    id: str
    ticket_id: str
    title: str
    description: str
    category: str
    problem_domain: str = "technical"
    location_type: str = "campus"
    subcategory: Optional[str] = None
    priority: TicketPriority
    status: TicketStatus
    campus_id: Optional[str] = None
    building: str
    floor: Optional[str] = None
    room: str
    department: Optional[str] = None
    affected_users: Optional[int] = 1
    attachments: List[str] = []

    created_by: Dict[str, Any]
    assigned_to: Optional[Dict[str, Any]] = None

    created_at: str
    updated_at: str

    sla_deadline: Optional[str] = None
    sla_target_hours: Optional[int] = 24
    is_overdue: bool = False
    time_remaining_minutes: Optional[int] = None

    first_response_at: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    resolution_notes: Optional[str] = None
    hold_reason: Optional[str] = None

    timeline: List[TimelineEvent] = []
    has_feedback: bool = False
    linked_incident_id: Optional[str] = None
