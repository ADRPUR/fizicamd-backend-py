import re
import unicodedata
import uuid
from datetime import datetime, timezone
from sqlalchemy import func, String, cast
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, NotFoundError
from app.models.resource_category import ResourceCategory
from app.models.resource_entry import ResourceEntry
from app.models.user import User
from app.models.user_profile import UserProfile

ALLOWED_BLOCK_TYPES = {"TEXT", "LINK", "IMAGE", "PDF", "FORMULA"}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    normalized = normalized.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or str(uuid.uuid4())


def resolve_category_code(db: Session, label: str) -> str:
    base = slugify(label)
    candidate = base
    counter = 2
    while db.query(ResourceCategory).filter(ResourceCategory.code == candidate).first():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def list_categories(db: Session) -> list[ResourceCategory]:
    return (
        db.query(ResourceCategory)
        .order_by(ResourceCategory.group_order.asc(), ResourceCategory.sort_order.asc())
        .all()
    )


def resolve_group_order(db: Session, group_label: str, preferred: int | None, fallback: int | None) -> int:
    if preferred is not None:
        return preferred
    if fallback is not None:
        return fallback
    existing = db.query(ResourceCategory).filter(ResourceCategory.group_label == group_label).first()
    if existing:
        return existing.group_order
    max_value = db.query(func.max(ResourceCategory.group_order)).scalar()
    return (max_value or 0) + 1


def resolve_sort_order(db: Session, group_label: str, preferred: int | None, fallback: int | None) -> int:
    if preferred is not None:
        return preferred
    if fallback is not None:
        return fallback
    max_value = (
        db.query(func.max(ResourceCategory.sort_order))
        .filter(ResourceCategory.group_label == group_label)
        .scalar()
    )
    return (max_value or 0) + 1


def create_category(db: Session, label: str, group_label: str, sort_order: int | None, group_order: int | None) -> ResourceCategory:
    normalized_label = normalize_required(label, "Denumirea categoriei este obligatorie.")
    normalized_group = normalize_required(group_label, "Denumirea grupului este obligatorie.")
    category = ResourceCategory(
        id=uuid.uuid4(),
        code=resolve_category_code(db, normalized_label),
        label=normalized_label,
        group_label=normalized_group,
        group_order=resolve_group_order(db, normalized_group, group_order, None),
        sort_order=resolve_sort_order(db, normalized_group, sort_order, None),
        created_at=datetime.now(timezone.utc),
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, code: str, label: str, group_label: str, sort_order: int | None, group_order: int | None) -> ResourceCategory:
    category = db.query(ResourceCategory).filter(ResourceCategory.code == code).first()
    if not category:
        raise NotFoundError("Categoria nu există.")
    normalized_label = normalize_required(label, "Denumirea categoriei este obligatorie.")
    normalized_group = normalize_required(group_label, "Denumirea grupului este obligatorie.")
    moving_group = category.group_label != normalized_group
    category.label = normalized_label
    category.group_label = normalized_group
    category.group_order = resolve_group_order(
        db,
        normalized_group,
        group_order if not moving_group else None,
        category.group_order if not moving_group else None,
    )
    if sort_order is not None:
        category.sort_order = sort_order
    elif moving_group:
        category.sort_order = resolve_sort_order(db, normalized_group, None, None)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, code: str):
    category = db.query(ResourceCategory).filter(ResourceCategory.code == code).first()
    if not category:
        raise NotFoundError("Categoria nu există.")
    if db.query(ResourceEntry).filter(ResourceEntry.category_code == code).first():
        raise BadRequestError("Nu poți șterge această categorie deoarece există resurse asociate.")
    db.delete(category)
    db.commit()


def update_group(db: Session, current_label: str, new_label: str, group_order: int | None) -> list[ResourceCategory]:
    normalized_current = normalize_required(current_label, "Grupul selectat este invalid.")
    normalized_new = normalize_required(new_label, "Denumirea grupului este obligatorie.")
    categories = db.query(ResourceCategory).filter(ResourceCategory.group_label == normalized_current).all()
    if not categories:
        raise NotFoundError("Grupul nu există.")
    resolved_order = group_order if group_order is not None else categories[0].group_order
    for cat in categories:
        cat.group_label = normalized_new
        cat.group_order = resolved_order
    db.commit()
    return categories


def list_published_page(db: Session, category_code: str | None, page: int, size: int):
    query = db.query(ResourceEntry).filter(ResourceEntry.status == "PUBLISHED")
    if category_code:
        query = query.filter(ResourceEntry.category_code == category_code)
    total = query.count()
    items = (
        query.order_by(ResourceEntry.published_at.desc())
        .offset(page * size)
        .limit(size)
        .all()
    )
    return items, total


def list_teacher_resources(db: Session, author_id: str, can_manage_others: bool):
    if can_manage_others:
        return db.query(ResourceEntry).order_by(ResourceEntry.created_at.desc()).all()
    return (
        db.query(ResourceEntry)
        .filter(ResourceEntry.author_id == author_id)
        .order_by(ResourceEntry.created_at.desc())
        .all()
    )


def get_resource_by_id(db: Session, resource_id: str) -> ResourceEntry | None:
    try:
        resource_uuid = uuid.UUID(resource_id)
    except ValueError:
        return None
    return db.query(ResourceEntry).filter(ResourceEntry.id == resource_uuid).first()


def get_resource_by_slug(db: Session, slug: str) -> ResourceEntry | None:
    return db.query(ResourceEntry).filter(ResourceEntry.slug == slug, ResourceEntry.status == "PUBLISHED").first()


def create_resource(db: Session, payload: dict, author_id: str) -> ResourceEntry:
    category = db.query(ResourceCategory).filter(ResourceCategory.code == payload["category_code"]).first()
    if not category:
        raise BadRequestError("Categoria selectată nu există.")
    title = (payload.get("title") or "").strip()
    summary = (payload.get("summary") or "").strip()
    if not title or not summary:
        raise BadRequestError("Titlul și descrierea sunt obligatorii.")
    status = payload.get("status") or "PUBLISHED"
    now = datetime.now(timezone.utc)
    author_uuid = uuid.UUID(author_id)
    entry = ResourceEntry(
        id=uuid.uuid4(),
        category_code=category.code,
        author_id=author_uuid,
        title=title,
        slug=resolve_resource_slug(db, title),
        summary=summary,
        avatar_media_id=payload.get("avatar_asset_id"),
        content=validate_blocks(payload.get("blocks")),
        tags=clean_tags(payload.get("tags")),
        status=status,
        published_at=now if status == "PUBLISHED" else None,
        created_at=now,
        updated_at=now,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def update_resource(db: Session, entry: ResourceEntry, payload: dict, actor_id: str, can_manage_others: bool):
    if not can_manage_others and str(entry.author_id) != actor_id:
        raise NotFoundError("Resursa nu a fost găsită.")
    category = db.query(ResourceCategory).filter(ResourceCategory.code == payload["category_code"]).first()
    if not category:
        raise BadRequestError("Categoria selectată nu există.")
    title = (payload.get("title") or "").strip()
    summary = (payload.get("summary") or "").strip()
    if not title or not summary:
        raise BadRequestError("Titlul și descrierea sunt obligatorii.")
    now = datetime.now(timezone.utc)
    status = payload.get("status") or entry.status
    entry.category_code = category.code
    entry.title = title
    entry.summary = summary
    entry.avatar_media_id = payload.get("avatar_asset_id")
    entry.content = validate_blocks(payload.get("blocks"))
    entry.tags = clean_tags(payload.get("tags"))
    entry.status = status
    if status == "PUBLISHED":
        if entry.published_at is None:
            entry.published_at = now
    else:
        entry.published_at = None
    entry.updated_at = now
    db.commit()
    db.refresh(entry)
    return entry


def delete_resource(db: Session, entry: ResourceEntry, actor_id: str, can_manage_others: bool):
    if not can_manage_others and str(entry.author_id) != actor_id:
        raise NotFoundError("Resursa nu a fost găsită.")
    db.delete(entry)
    db.commit()


def search_published(db: Session, term: str, limit: int) -> list[ResourceEntry]:
    cleaned = term.strip()
    if not cleaned:
        return []
    size = max(1, min(limit, 20))
    like = f"%{cleaned}%"
    return (
        db.query(ResourceEntry)
        .filter(ResourceEntry.status == "PUBLISHED")
        .filter(
            (ResourceEntry.title.ilike(like))
            | (ResourceEntry.summary.ilike(like))
            | (cast(ResourceEntry.tags, String).ilike(like))
        )
        .order_by(ResourceEntry.published_at.desc())
        .limit(size)
        .all()
    )


def author_display_name(db: Session, author_id: str) -> str:
    try:
        author_uuid = uuid.UUID(author_id)
    except ValueError:
        return "Profesor"
    user = db.query(User).filter(User.id == author_uuid).first()
    if not user:
        return "Profesor"
    profile = db.query(UserProfile).filter(UserProfile.user_id == author_uuid).first()
    if profile and (profile.first_name or profile.last_name):
        return f"{profile.first_name or ''} {profile.last_name or ''}".strip()
    return user.email


def resolve_resource_slug(db: Session, title: str) -> str:
    base = slugify(title)
    candidate = base
    counter = 2
    while db.query(ResourceEntry).filter(ResourceEntry.slug == candidate).first():
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def clean_tags(tags: list | None) -> list[str]:
    if not tags:
        return []
    cleaned = []
    for tag in tags:
        value = (tag or "").strip()
        if not value:
            continue
        if value not in cleaned:
            cleaned.append(value)
        if len(cleaned) >= 12:
            break
    return cleaned


def validate_blocks(blocks: list | None) -> list[dict]:
    if not blocks:
        return []
    cleaned = []
    for block in blocks:
        payload = block.model_dump() if hasattr(block, "model_dump") else block or {}
        block_type = (payload.get("type") or "").upper()
        if block_type not in ALLOWED_BLOCK_TYPES:
            continue
        if block_type == "TEXT":
            text = (payload.get("text") or "").strip()
            if text:
                cleaned.append({"type": "TEXT", "text": text, "title": payload.get("title")})
        elif block_type == "LINK":
            url = (payload.get("url") or "").strip()
            if url:
                cleaned.append(
                    {
                        "type": "LINK",
                        "url": url,
                        "title": payload.get("title") or "Link",
                    }
                )
        elif block_type in {"IMAGE", "PDF"}:
            asset_id = payload.get("asset_id") or payload.get("assetId")
            if not asset_id:
                raise BadRequestError("Încărcarea fișierului pentru blocurile media este obligatorie.")
            caption = payload.get("caption")
            title = payload.get("title")
            cleaned.append(
                {
                    "type": block_type,
                    "assetId": asset_id,
                    "caption": caption,
                    "title": title,
                }
            )
        elif block_type == "FORMULA":
            text = (payload.get("text") or "").strip()
            if not text:
                raise BadRequestError("Formula nu poate fi goală.")
            cleaned.append({"type": "FORMULA", "text": text, "title": payload.get("title")})
    return cleaned


def normalize_required(value: str | None, message: str) -> str:
    trimmed = (value or "").strip()
    if not trimmed:
        raise BadRequestError(message)
    return trimmed
