from typing import Optional, List, Dict, Any, Annotated
import re
from pydantic import BaseModel, Field, field_validator

class CommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)
    is_internal: bool = False  # Internal notes can only be posted/seen by staff & admin
    attachments: Optional[List[Annotated[str, Field(max_length=2048)]]] = Field(default_factory=list, max_length=5)

    @field_validator("attachments")
    @classmethod
    def validate_attachment_urls(cls, values):
        for value in values or []:
            if not (value.startswith("https://") or re.fullmatch(r"/api/uploads/[a-f0-9]{32}", value)):
                raise ValueError("Attachments must use secure HTTPS URLs.")
        return values

class CommentResponse(BaseModel):
    id: str
    ticket_id: str
    author: Dict[str, Any]
    content: str
    is_internal: bool = False
    attachments: List[str] = []
    created_at: str
