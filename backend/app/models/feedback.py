from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class FeedbackCreate(BaseModel):
    ticket_id: str = Field(..., min_length=1, max_length=100)
    rating: int = Field(..., ge=1, le=5)
    comments: Optional[str] = Field(default=None, max_length=2000)

class FeedbackResponse(BaseModel):
    id: str
    ticket_id: str
    ticket_custom_id: str
    rating: int
    comments: Optional[str] = Field(default=None, max_length=2000)
    created_by: Dict[str, Any]
    created_at: str
