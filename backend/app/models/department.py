from typing import Optional, List
from pydantic import BaseModel, Field

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    code: str = Field(..., min_length=2, max_length=20)
    building_id: Optional[str] = None
    head_of_department: Optional[str] = None
    is_active: bool = True

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentResponse(DepartmentBase):
    id: str

class StaffAssignmentBase(BaseModel):
    ticket_id: str
    staff_id: str
    assigned_by: str
    assigned_at: str
    assignment_type: str = "manual"  # manual or auto
    scoring_breakdown: Optional[dict] = None

class IncidentBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    description: str
    category: str
    building: Optional[str] = None
    affected_services: List[str] = []
    status: str = "investigating"  # investigating, identified, monitoring, resolved
    severity: str = "major"  # minor, major, critical
    linked_ticket_ids: List[str] = []
    created_by: str
    created_at: str
    updated_at: str
    resolved_at: Optional[str] = None

class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    description: str
    category: str
    building: Optional[str] = None
    severity: Optional[str] = "major"
    affected_services: Optional[List[str]] = []

class IncidentResponse(IncidentBase):
    id: str
