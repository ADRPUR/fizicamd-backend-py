from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_any_role, get_current_user
from app.schemas.resources import TeacherResourceListResponse, ResourceDetailDto, CreateResourceRequest, UpdateResourceRequest
from app.services.resources import (
    list_teacher_resources,
    get_resource_by_id,
    create_resource,
    update_resource,
    delete_resource,
    author_display_name,
)
from app.services.media import build_asset_url
from app.services.users import has_role
from app.models.resource_category import ResourceCategory

router = APIRouter(prefix="/teacher/resources", tags=["teacher-resources"], dependencies=[Depends(require_any_role("TEACHER", "ADMIN"))])


def to_category(db: Session, code: str):
    cat = db.query(ResourceCategory).filter(ResourceCategory.code == code).first()
    if not cat:
        return None
    return {
        "code": cat.code,
        "label": cat.label,
        "group": cat.group_label,
        "sort_order": cat.sort_order,
        "group_order": cat.group_order,
    }


@router.get("", response_model=TeacherResourceListResponse)
def list_resources(user=Depends(get_current_user), db: Session = Depends(get_db)):
    can_manage_others = has_role(db, str(user.id), "ADMIN")
    items = list_teacher_resources(db, str(user.id), can_manage_others)
    cards = []
    for entry in items:
        cards.append(
            {
                "id": str(entry.id),
                "title": entry.title,
                "slug": entry.slug,
                "summary": entry.summary,
                "category": to_category(db, entry.category_code),
                "avatar_url": build_asset_url(entry.avatar_media_id) if entry.avatar_media_id else None,
                "tags": entry.tags or [],
                "author_name": author_display_name(db, str(entry.author_id)),
                "published_at": entry.published_at.isoformat() if entry.published_at else None,
                "status": entry.status,
            }
        )
    return TeacherResourceListResponse(items=cards)


@router.post("", response_model=ResourceDetailDto)
def create(payload: CreateResourceRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    entry = create_resource(db, payload.model_dump(), str(user.id))
    return ResourceDetailDto(
        id=str(entry.id),
        title=entry.title,
        slug=entry.slug,
        summary=entry.summary,
        category=to_category(db, entry.category_code),
        avatar_url=build_asset_url(entry.avatar_media_id) if entry.avatar_media_id else None,
        avatar_asset_id=str(entry.avatar_media_id) if entry.avatar_media_id else None,
        tags=entry.tags or [],
        author_name=author_display_name(db, str(entry.author_id)),
        published_at=entry.published_at.isoformat() if entry.published_at else None,
        status=entry.status,
        blocks=entry.content or [],
    )


@router.get("/{resource_id}", response_model=ResourceDetailDto)
def detail(resource_id: str, db: Session = Depends(get_db)):
    entry = get_resource_by_id(db, resource_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Resource not found")
    return ResourceDetailDto(
        id=str(entry.id),
        title=entry.title,
        slug=entry.slug,
        summary=entry.summary,
        category=to_category(db, entry.category_code),
        avatar_url=build_asset_url(entry.avatar_media_id) if entry.avatar_media_id else None,
        avatar_asset_id=str(entry.avatar_media_id) if entry.avatar_media_id else None,
        tags=entry.tags or [],
        author_name=author_display_name(db, str(entry.author_id)),
        published_at=entry.published_at.isoformat() if entry.published_at else None,
        status=entry.status,
        blocks=entry.content or [],
    )


@router.put("/{resource_id}", response_model=ResourceDetailDto)
def update(resource_id: str, payload: UpdateResourceRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    entry = get_resource_by_id(db, resource_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Resource not found")
    can_manage_others = has_role(db, str(user.id), "ADMIN")
    entry = update_resource(db, entry, payload.model_dump(), str(user.id), can_manage_others)
    return ResourceDetailDto(
        id=str(entry.id),
        title=entry.title,
        slug=entry.slug,
        summary=entry.summary,
        category=to_category(db, entry.category_code),
        avatar_url=build_asset_url(entry.avatar_media_id) if entry.avatar_media_id else None,
        avatar_asset_id=str(entry.avatar_media_id) if entry.avatar_media_id else None,
        tags=entry.tags or [],
        author_name=author_display_name(db, str(entry.author_id)),
        published_at=entry.published_at.isoformat() if entry.published_at else None,
        status=entry.status,
        blocks=entry.content or [],
    )


@router.delete("/{resource_id}")
def remove(resource_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    entry = get_resource_by_id(db, resource_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Resource not found")
    can_manage_others = has_role(db, str(user.id), "ADMIN")
    delete_resource(db, entry, str(user.id), can_manage_others)
    return None
