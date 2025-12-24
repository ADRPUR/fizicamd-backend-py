from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional


class SearchResultItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: str
    title: str
    slug: str
    href: Optional[str] = None
    type: str
    parent_id: Optional[str] = Field(default=None, alias="parentId")


class SearchResponse(BaseModel):
    items: List[SearchResultItem]


class VisitRequest(BaseModel):
    path: Optional[str] = None
    referrer: Optional[str] = None


class VisitCountResponse(BaseModel):
    total: int
