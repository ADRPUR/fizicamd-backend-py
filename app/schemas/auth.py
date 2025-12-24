from pydantic import BaseModel, EmailStr, Field
from pydantic import ConfigDict
from typing import List, Optional


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: Optional[str] = Field(default=None, alias="confirmPassword")
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    phone: Optional[str] = None
    birth_date: Optional[str] = Field(default=None, alias="birthDate")
    school: Optional[str] = None
    grade_level: Optional[str] = Field(default=None, alias="gradeLevel")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    access_token: str = Field(alias="accessToken")
    refresh_token: str = Field(alias="refreshToken")
    expires_at: int = Field(alias="expiresAt")
    user: "UserDto"


class RefreshRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    refresh_token: str = Field(alias="refreshToken")


class RegisterResponse(BaseModel):
    user_id: str
    email: EmailStr


class UserDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    email: EmailStr
    status: str
    role: str
    roles: List[str]
    profile: Optional["UserProfileDto"] = None
    last_login_at: Optional[str] = Field(default=None, alias="lastLoginAt")


class UserProfileDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    first_name: Optional[str] = Field(default=None, alias="firstName")
    last_name: Optional[str] = Field(default=None, alias="lastName")
    phone: Optional[str] = None
    school: Optional[str] = None
    grade_level: Optional[str] = Field(default=None, alias="gradeLevel")
    birth_date: Optional[str] = Field(default=None, alias="birthDate")
    gender: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")


TokenResponse.model_rebuild()
