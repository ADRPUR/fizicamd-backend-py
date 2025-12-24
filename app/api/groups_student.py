from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role, get_current_user
from app.schemas.groups import GroupResponse
from app.services.groups import my_groups, get_group_view

router = APIRouter(
    prefix="/student/groups",
    tags=["student-groups"],
    dependencies=[Depends(require_role("STUDENT"))],
)


@router.get("", response_model=list[GroupResponse])
def list_groups(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return my_groups(db, str(user.id))


@router.get("/{group_id}", response_model=GroupResponse)
def get(group_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_group_view(db, group_id, str(user.id), False)
