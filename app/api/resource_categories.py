from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_any_role
from app.schemas.resources import CategoryDto, CategoryUpsertRequest, GroupUpdateRequest
from app.core.errors import BadRequestError, NotFoundError
from app.services.resources import list_categories, create_category, update_category, delete_category, update_group

router = APIRouter(prefix="/teacher/resource-categories", tags=["resource-categories"], dependencies=[Depends(require_any_role("TEACHER", "ADMIN"))])


def to_dto(cat) -> CategoryDto:
    return CategoryDto(
        code=cat.code,
        label=cat.label,
        group=cat.group_label,
        sort_order=cat.sort_order,
        group_order=cat.group_order,
    )


@router.get("", response_model=list[CategoryDto])
def list_all(db: Session = Depends(get_db)):
    return [to_dto(cat) for cat in list_categories(db)]


@router.post("", response_model=CategoryDto)
def create(payload: CategoryUpsertRequest, db: Session = Depends(get_db)):
    cat = create_category(db, payload.label, payload.group, payload.sort_order, payload.group_order)
    return to_dto(cat)


@router.put("/{code}", response_model=CategoryDto)
def update(code: str, payload: CategoryUpsertRequest, db: Session = Depends(get_db)):
    try:
        cat = update_category(db, code, payload.label, payload.group, payload.sort_order, payload.group_order)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return to_dto(cat)


@router.delete("/{code}")
def delete(code: str, db: Session = Depends(get_db)):
    try:
        delete_category(db, code)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return None


@router.put("/groups/{group_label}", response_model=list[CategoryDto])
def update_group_label(group_label: str, payload: GroupUpdateRequest, db: Session = Depends(get_db)):
    try:
        cats = update_group(db, group_label, payload.label, payload.group_order)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return [to_dto(cat) for cat in cats]
