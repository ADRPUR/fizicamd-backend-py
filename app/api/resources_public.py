from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.resources import ResourceListResponse, ResourceDetailDto, CategoryDto
from app.services.resources import list_categories, list_published_page, get_resource_by_slug, author_display_name
from app.services.media import build_asset_url
from app.models.resource_category import ResourceCategory
from app.models.resource_entry import ResourceEntry

router = APIRouter(prefix="/public/resources", tags=["public-resources"])


def to_category(cat: ResourceCategory | None) -> CategoryDto | None:
    if not cat:
        return None
    return CategoryDto(
        code=cat.code,
        label=cat.label,
        group=cat.group_label,
        sort_order=cat.sort_order,
        group_order=cat.group_order,
    )


@router.get("/categories", response_model=list[CategoryDto])
def categories(db: Session = Depends(get_db)):
    return [to_category(cat) for cat in list_categories(db)]


@router.get("", response_model=ResourceListResponse)
def resources(
    category: str | None = Query(default=None),
    limit: int = Query(default=9, ge=1, le=30),
    page: int = Query(default=1, ge=1),
    db: Session = Depends(get_db),
):
    items, total = list_published_page(db, category, page - 1, limit)
    cards = []
    for entry in items:
        cat = db.query(ResourceCategory).filter(ResourceCategory.code == entry.category_code).first()
        cards.append(
            {
                "id": str(entry.id),
                "title": entry.title,
                "slug": entry.slug,
                "summary": entry.summary,
                "category": to_category(cat),
                "avatar_url": build_asset_url(entry.avatar_media_id) if entry.avatar_media_id else None,
                "tags": entry.tags or [],
                "author_name": author_display_name(db, str(entry.author_id)),
                "published_at": entry.published_at.isoformat() if entry.published_at else None,
                "status": entry.status,
            }
        )
    return ResourceListResponse(items=cards, total=total, page=page, size=limit)


@router.get("/{slug}", response_model=ResourceDetailDto)
def detail(slug: str, db: Session = Depends(get_db)):
    entry = get_resource_by_slug(db, slug)
    if not entry:
        raise HTTPException(status_code=404, detail="Resource not found")
    cat = db.query(ResourceCategory).filter(ResourceCategory.code == entry.category_code).first()
    return ResourceDetailDto(
        id=str(entry.id),
        title=entry.title,
        slug=entry.slug,
        summary=entry.summary,
        category=to_category(cat),
        avatar_url=build_asset_url(entry.avatar_media_id) if entry.avatar_media_id else None,
        avatar_asset_id=str(entry.avatar_media_id) if entry.avatar_media_id else None,
        tags=entry.tags or [],
        author_name=author_display_name(db, str(entry.author_id)),
        published_at=entry.published_at.isoformat() if entry.published_at else None,
        status=entry.status,
        blocks=entry.content or [],
    )
