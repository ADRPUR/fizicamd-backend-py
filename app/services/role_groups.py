import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.role import Role
from app.models.user_role import UserRole

ROLE_CODES = ("ADMIN", "TEACHER", "STUDENT")


def _role_group_name(code: str) -> str:
    return f"Role: {code}"


def ensure_role_group(db: Session, code: str) -> Group:
    name = _role_group_name(code)
    group = db.query(Group).filter(Group.name == name).first()
    if group:
        return group
    now = datetime.now(timezone.utc)
    group = Group(
        id=uuid.uuid4(),
        name=name,
        description=f"System generated group for role {code}",
        visibility="SYSTEM",
        created_at=now,
        updated_at=now,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def ensure_all_role_groups_exist(db: Session):
    for code in ROLE_CODES:
        ensure_role_group(db, code)


def ensure_membership(db: Session, user_id: str, code: str):
    role_code = code.upper()
    group = ensure_role_group(db, role_code)
    existing = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group.id, GroupMember.user_id == user_id)
        .first()
    )
    if existing:
        return
    now = datetime.now(timezone.utc)
    member = GroupMember(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=user_id,
        member_role=role_code,
        status="ACTIVE",
        joined_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(member)
    db.commit()


def ensure_user_memberships(db: Session, user_id: str):
    roles = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    for role in roles:
        ensure_membership(db, user_id, role[0])
