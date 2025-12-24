from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role, get_current_user
from app.schemas.groups import UpdateGroupRequest, AddMemberRequest, GroupResponse
from app.services.groups import (
    my_groups,
    get_group_view,
    update_group,
    add_member,
    remove_member,
)

router = APIRouter(
    prefix="/teacher/groups",
    tags=["teacher-groups"],
    dependencies=[Depends(require_role("TEACHER"))],
)


@router.get("", response_model=list[GroupResponse])
def list_groups(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return my_groups(db, str(user.id))


@router.get("/{group_id}", response_model=GroupResponse)
def get(group_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return get_group_view(db, group_id, str(user.id), False)


@router.put("/{group_id}", status_code=204)
def update(group_id: str, payload: UpdateGroupRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    update_group(db, group_id, payload.name, payload.grade, payload.year, str(user.id), False)
    return None


@router.post("/{group_id}/members", status_code=204)
def add(group_id: str, payload: AddMemberRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    add_member(db, group_id, payload.user_id, payload.member_role, str(user.id), False)
    return None


@router.delete("/{group_id}/members/{user_id}", status_code=204)
def remove(group_id: str, user_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    remove_member(db, group_id, user_id, str(user.id), False)
    return None
