from pydantic import BaseModel, Field

class SLAPolicyBase(BaseModel):
    priority: str
    target_resolution_hours: int = Field(..., ge=1)
    target_response_hours: int = Field(..., ge=1)
    description: str

class SLAPolicyCreate(SLAPolicyBase):
    pass

class SLAPolicyResponse(SLAPolicyBase):
    id: str
    updated_at: str
