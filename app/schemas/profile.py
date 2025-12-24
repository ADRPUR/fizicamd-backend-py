from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    first_name: Optional[str] = Field(default=None, max_length=120, alias="firstName")
    last_name: Optional[str] = Field(default=None, max_length=120, alias="lastName")
    birth_date: Optional[str] = Field(default=None, alias="birthDate")
    gender: Optional[str] = Field(default=None, max_length=16)
    phone: Optional[str] = Field(default=None, max_length=64)
    school: Optional[str] = Field(default=None, max_length=255)
    grade_level: Optional[str] = Field(default=None, max_length=32, alias="gradeLevel")
    bio: Optional[str] = Field(default=None, max_length=1024)


class ChangePasswordRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    current_password: str = Field(min_length=8, max_length=128, alias="currentPassword")
    new_password: str = Field(min_length=8, max_length=128, alias="newPassword")
    confirm_password: str = Field(min_length=8, max_length=128, alias="confirmPassword")
