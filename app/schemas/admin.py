from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import List, Optional


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    email: EmailStr
    status: str
    primary_role: str = Field(alias="primaryRole")
    roles: List[str]
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    phone: Optional[str] = None
    school: Optional[str] = None
    grade_level: Optional[str] = Field(default=None, alias="gradeLevel")
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    last_login_at: Optional[str] = Field(default=None, alias="lastLoginAt")
    last_seen_at: Optional[str] = Field(default=None, alias="lastSeenAt")


class AdminUserCreateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    roles: List[str]
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    phone: Optional[str] = None
    school: Optional[str] = None
    grade_level: Optional[str] = Field(default=None, alias="gradeLevel")
    status: Optional[str] = None


class AdminUserUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    email: EmailStr
    roles: List[str]
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    phone: Optional[str] = None
    school: Optional[str] = None
    grade_level: Optional[str] = Field(default=None, alias="gradeLevel")
    status: Optional[str] = None


class PagedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    items: list
    total: int
    page: int
    page_size: int = Field(alias="pageSize")


class AssignRoleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    role: str
