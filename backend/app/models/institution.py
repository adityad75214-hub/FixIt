from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator


class InstitutionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    slug: str = Field(..., min_length=2, max_length=60, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email_domains: List[str] = Field(default_factory=list, max_length=20)

    @field_validator("email_domains")
    @classmethod
    def normalize_domains(cls, values):
        result = []
        for value in values:
            domain = value.strip().lower().lstrip("@")
            if not domain or "." not in domain or "@" in domain or len(domain) > 253:
                raise ValueError("Enter valid email domains such as college.edu")
            result.append(domain)
        return sorted(set(result))


class InstitutionResponse(BaseModel):
    id: str
    name: str
    slug: str
    email_domains: List[str] = []
    status: str = "active"


class InstitutionAdminCreate(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    name: str = Field(..., min_length=2, max_length=120)
    password: str = Field(..., min_length=12, max_length=128)


class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    email_domains: Optional[List[str]] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, pattern="^(active|suspended)$")

    @field_validator("email_domains")
    @classmethod
    def normalize_domains(cls, values):
        if values is None:
            return values
        result = []
        for value in values:
            domain = value.strip().lower().lstrip("@")
            if not domain or "." not in domain or "@" in domain or len(domain) > 253:
                raise ValueError("Enter valid email domains such as college.edu")
            result.append(domain)
        return sorted(set(result))
