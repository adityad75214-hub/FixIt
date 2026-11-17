from datetime import datetime, timezone
from typing import Optional, List, Annotated
from enum import Enum
from pydantic import BaseModel, EmailStr, Field

class UserRole(str, Enum):
    STUDENT = "student"
    FACULTY = "faculty"
    STAFF = "staff"
    ADMIN = "admin"
    PLATFORM_ADMIN = "platform_admin"

class UserBase(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    name: str = Field(..., min_length=1, max_length=120)
    role: UserRole = UserRole.STUDENT
    department: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=30)
    identifier: Optional[str] = Field(default=None, max_length=100)  # Roll number or Faculty/Staff ID
    specialization: Optional[List[str]] = Field(default=None, max_length=20)  # For IT Staff
    avatar_url: Optional[str] = Field(default=None, max_length=2048)

class UserCreate(UserBase):
    password: str = Field(..., min_length=12, max_length=128)
    institution_slug: Optional[str] = Field(default=None, min_length=2, max_length=60)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    password: str = Field(..., min_length=1, max_length=128)

class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    phone: Optional[str] = Field(default=None, max_length=30)
    department: Optional[str] = Field(default=None, max_length=100)
    avatar_url: Optional[str] = Field(default=None, max_length=2048)
    specialization: Optional[List[Annotated[str, Field(max_length=80)]]] = None
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None

class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=12, max_length=128)

class UserResponse(UserBase):
    id: str
    is_active: bool = True
    created_at: str
    active_tickets_count: Optional[int] = 0
    institution_id: Optional[str] = None
    institution_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class UserPreferences(BaseModel):
    email_notifications: bool = True
    in_app_notifications: bool = True
    language: str = Field(default="en", pattern="^(en|hi|kn|ta|te|ml|mr|bn)$")
