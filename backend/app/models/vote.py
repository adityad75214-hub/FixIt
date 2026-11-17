from typing import Optional
from pydantic import BaseModel

class ArticleVote(BaseModel):
    helpful: bool = True
