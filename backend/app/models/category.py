from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

class CategoryBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    description: Optional[str] = Field(default=None, max_length=300)
    subcategories: List[str] = Field(default_factory=list, max_length=100)
    is_active: bool = True
    icon: Optional[str] = Field(default="Wrench", max_length=40)

    @field_validator("name")
    @classmethod
    def normalize_category_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Category name cannot be blank.")
        return cleaned

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: str

class CampusLocationBase(BaseModel):
    building: str
    floors: List[str] = Field(default_factory=lambda: ["Ground", "1st", "2nd", "3rd"], max_length=100)
    rooms: List[str] = Field(default_factory=list, max_length=500)
    is_active: bool = True

class CampusLocationResponse(CampusLocationBase):
    id: str
