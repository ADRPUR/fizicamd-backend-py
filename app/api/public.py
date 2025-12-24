import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.public import SearchResponse, SearchResultItem, VisitRequest, VisitCountResponse
from app.services.resources import search_published
from app.models.site_visit import SiteVisit

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/search", response_model=SearchResponse)
def search(q: str | None = None, db: Session = Depends(get_db)):
    results = search_published(db, q or "", 20)
    items = [
        SearchResultItem(
            id=str(r.id),
            title=r.title,
            slug=r.slug,
            href=None,
            type="RESOURCE",
            parent_id=None,
        )
        for r in results
    ]
    return SearchResponse(items=items)


@router.post("/visits")
def track_visit(payload: VisitRequest | None, request: Request, db: Session = Depends(get_db)):
    ip = resolve_client_ip(request)
    ua = trim(request.headers.get("User-Agent"), 512)
    path = trim(payload.path if payload else None, 255)
    referrer = trim(payload.referrer if payload else None, 512)
    visit = SiteVisit(
        id=uuid.uuid4(),
        ip_address=ip,
        user_agent=ua,
        path=path,
        referrer=referrer,
        created_at=datetime.now(timezone.utc),
    )
    db.add(visit)
    db.commit()
    return None


@router.get("/visits/count", response_model=VisitCountResponse)
def visit_count(db: Session = Depends(get_db)):
    total = db.query(SiteVisit).count()
    return VisitCountResponse(total=total)


def resolve_client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        comma = forwarded.find(",")
        return trim(forwarded[:comma] if comma >= 0 else forwarded, 512)
    return trim(request.client.host if request.client else None, 512)


def trim(value: str | None, max_len: int) -> str | None:
    if not value:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned[:max_len]
