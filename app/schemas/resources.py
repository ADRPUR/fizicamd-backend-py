from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class CategoryDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    code: str
    label: str
    group: str
    sort_order: int = Field(alias="sortOrder")
    group_order: int = Field(alias="groupOrder")


class ResourceBlockDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type: str
    text: Optional[str] = None
    url: Optional[str] = None
    asset_id: Optional[str] = Field(default=None, alias="assetId")
    media_url: Optional[str] = Field(default=None, alias="mediaUrl")
    caption: Optional[str] = None
    title: Optional[str] = None


class ResourceCardDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    title: str
    slug: str
    summary: str
    category: Optional[CategoryDto] = None
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    tags: List[str]
    author_name: str = Field(alias="authorName")
    published_at: Optional[str] = Field(default=None, alias="publishedAt")
    status: Optional[str] = None


class ResourceDetailDto(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    title: str
    slug: str
    summary: str
    category: Optional[CategoryDto] = None
    avatar_url: Optional[str] = Field(default=None, alias="avatarUrl")
    avatar_asset_id: Optional[str] = Field(default=None, alias="avatarAssetId")
    tags: List[str]
    author_name: str = Field(alias="authorName")
    published_at: Optional[str] = Field(default=None, alias="publishedAt")
    status: Optional[str] = None
    blocks: List[ResourceBlockDto]


class ResourceListResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    items: List[ResourceCardDto]
    total: int
    page: int
    size: int


class TeacherResourceListResponse(BaseModel):
    items: List[ResourceCardDto]


class ResourceBlockInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    type: str
    text: Optional[str] = None
    url: Optional[str] = None
    asset_id: Optional[str] = Field(default=None, alias="assetId")
    caption: Optional[str] = None
    title: Optional[str] = None


class CreateResourceRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    category_code: str = Field(min_length=1, alias="categoryCode")
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    avatar_asset_id: Optional[str] = Field(default=None, alias="avatarAssetId")
    tags: List[str] = []
    blocks: List[ResourceBlockInput] = []
    status: str


class UpdateResourceRequest(CreateResourceRequest):
    pass


class CategoryUpsertRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    label: str
    group: str
    sort_order: Optional[int] = Field(default=None, alias="sortOrder")
    group_order: Optional[int] = Field(default=None, alias="groupOrder")


class GroupUpdateRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    label: str
    group_order: Optional[int] = Field(default=None, alias="groupOrder")
