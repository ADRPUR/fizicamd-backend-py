from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class CreateGroupRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    grade: Optional[int] = None
    year: Optional[int] = None


class UpdateGroupRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: Optional[str] = None
    grade: Optional[int] = None
    year: Optional[int] = None


class AddMemberRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    user_id: str = Field(alias="userId")
    member_role: str = Field(alias="memberRole")


class MemberResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    user_id: str = Field(alias="userId")
    email: str
    member_role: str = Field(alias="memberRole")


class GroupResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    name: str
    grade: Optional[int] = None
    year: Optional[int] = None
    created_at: Optional[str] = Field(default=None, alias="createdAt")
    members: List[MemberResponse]
