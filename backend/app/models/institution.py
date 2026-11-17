from typing import List, Optional
import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class InstitutionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=160)
    slug: str = Field(..., min_length=2, max_length=60, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    email_domains: List[str] = Field(default_factory=list, max_length=20)
    student_email_domains: List[str] = Field(default_factory=list, max_length=20)
    faculty_email_domains: List[str] = Field(default_factory=list, max_length=20)
    student_identifier_pattern: Optional[str] = Field(default=None, max_length=120)
    faculty_identifier_pattern: Optional[str] = Field(default=None, max_length=120)

    @field_validator("email_domains", "student_email_domains", "faculty_email_domains")
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
    student_email_domains: List[str] = []
    faculty_email_domains: List[str] = []
    student_identifier_pattern: Optional[str] = None
    faculty_identifier_pattern: Optional[str] = None
    status: str = "active"


class InstitutionAdminInvite(BaseModel):
    email: EmailStr = Field(..., max_length=254)
    name: str = Field(..., min_length=2, max_length=120)
    designation: Optional[str] = Field(default=None, max_length=120)
    department: Optional[str] = Field(default=None, max_length=100)


class InstitutionAdminInviteAccept(BaseModel):
    token: str = Field(..., min_length=32, max_length=256)
    password: str = Field(..., min_length=12, max_length=128)


class InstitutionUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=160)
    email_domains: Optional[List[str]] = Field(default=None, max_length=20)
    student_email_domains: Optional[List[str]] = Field(default=None, max_length=20)
    faculty_email_domains: Optional[List[str]] = Field(default=None, max_length=20)
    student_identifier_pattern: Optional[str] = Field(default=None, max_length=120)
    faculty_identifier_pattern: Optional[str] = Field(default=None, max_length=120)
    status: Optional[str] = Field(default=None, pattern="^(active|suspended)$")

    @field_validator("email_domains", "student_email_domains", "faculty_email_domains")
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


class _IdentifierPatternValidation(BaseModel):
    student_identifier_pattern: Optional[str] = None
    faculty_identifier_pattern: Optional[str] = None

    @field_validator("student_identifier_pattern", "faculty_identifier_pattern")
    @classmethod
    def validate_pattern(cls, value):
        if value is None or value == "":
            return None
        if len(value) > 120:
            raise ValueError("Identifier pattern must be 120 characters or fewer.")
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError("Enter a valid identifier regular expression.") from exc
        return value
