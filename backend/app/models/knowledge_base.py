from typing import Optional, List, Annotated
from pydantic import BaseModel, Field

class KBArticleBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=150)
    category: str = Field(..., min_length=2, max_length=80)
    content: str = Field(..., min_length=20, max_length=10000)
    tags: List[Annotated[str, Field(max_length=40)]] = Field(default_factory=list, max_length=20)
    is_published: bool = True

class KBArticleCreate(KBArticleBase):
    pass

class KBArticleUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=5, max_length=150)
    category: Optional[str] = Field(default=None, min_length=2, max_length=80)
    content: Optional[str] = Field(default=None, min_length=20, max_length=10000)
    tags: Optional[List[Annotated[str, Field(max_length=40)]]] = Field(default=None, max_length=20)
    is_published: Optional[bool] = None

class KBArticleResponse(KBArticleBase):
    id: str
    views: int = 0
    helpful_count: int = 0
    not_helpful_count: int = 0
    author_name: str
    created_at: str
    updated_at: str
