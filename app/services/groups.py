import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.models.group import Group
from app.models.group_member import GroupMember
from app.models.user import User

ALLOWED_MEMBER_ROLES = {"ADMIN", "TEACHER", "STUDENT"}


def _require_role(role: str) -> str:
    code = (role or "").upper()
    if code not in ALLOWED_MEMBER_ROLES:
        raise BadRequestError("Invalid member role")
    return code


def _is_member(db: Session, group_id: str, user_id: str) -> bool:
    return (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
        is not None
    )


def _is_teacher_in_group(db: Session, group_id: str, user_id: str) -> bool:
    return (
        db.query(GroupMember)
        .filter(
            GroupMember.group_id == group_id,
            GroupMember.user_id == user_id,
            GroupMember.member_role == "TEACHER",
        )
        .first()
        is not None
    )


def create_group(db: Session, name: str, grade: int | None, year: int | None, actor_id: str, actor_is_admin: bool) -> str:
    if not actor_is_admin:
        raise ForbiddenError("Only ADMIN can create groups")
    if not name or not name.strip():
        raise BadRequestError("Name is required")
    now = datetime.now(timezone.utc)
    group = Group(
        id=uuid.uuid4(),
        name=name.strip(),
        grade=grade,
        year=year,
        visibility="PRIVATE",
        created_at=now,
        updated_at=now,
    )
    db.add(group)
    db.commit()
    return str(group.id)


def update_group(db: Session, group_id: str, name: str | None, grade: int | None, year: int | None, actor_id: str, actor_is_admin: bool):
    if not actor_is_admin and not _is_teacher_in_group(db, group_id, actor_id):
        raise ForbiddenError("Not allowed")
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise NotFoundError("Group not found")
    if name is not None:
        group.name = name.strip()
    group.grade = grade
    group.year = year
    group.updated_at = datetime.now(timezone.utc)
    db.commit()


def delete_group(db: Session, group_id: str, actor_id: str, actor_is_admin: bool):
    if not actor_is_admin:
        raise ForbiddenError("Only ADMIN can delete groups")
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise NotFoundError("Group not found")
    db.delete(group)
    db.commit()


def add_member(db: Session, group_id: str, user_id: str, member_role: str, actor_id: str, actor_is_admin: bool):
    role_code = _require_role(member_role)
    if not actor_is_admin:
        if not _is_teacher_in_group(db, group_id, actor_id):
            raise ForbiddenError("Teacher can manage only own groups")
        if role_code == "TEACHER":
            raise ForbiddenError("Teacher cannot grant TEACHER role")

    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise NotFoundError("Group not found")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")

    existing = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if existing:
        if actor_is_admin and existing.member_role != role_code:
            existing.member_role = role_code
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
        return

    now = datetime.now(timezone.utc)
    member = GroupMember(
        id=uuid.uuid4(),
        group_id=group.id,
        user_id=user.id,
        member_role=role_code,
        status="ACTIVE",
        joined_at=now,
        created_at=now,
        updated_at=now,
    )
    db.add(member)
    db.commit()


def remove_member(db: Session, group_id: str, user_id: str, actor_id: str, actor_is_admin: bool):
    member = (
        db.query(GroupMember)
        .filter(GroupMember.group_id == group_id, GroupMember.user_id == user_id)
        .first()
    )
    if not member:
        raise NotFoundError("Member not found")
    if not actor_is_admin:
        if not _is_teacher_in_group(db, group_id, actor_id):
            raise ForbiddenError("Teacher can manage only own groups")
        if member.member_role != "STUDENT":
            raise ForbiddenError("Teacher can remove only students")
    db.delete(member)
    db.commit()


def my_groups(db: Session, actor_id: str):
    group_ids = (
        db.query(GroupMember.group_id)
        .filter(GroupMember.user_id == actor_id)
        .distinct()
        .all()
    )
    ids = [gid[0] for gid in group_ids]
    return [get_group_view(db, group_id, actor_id, True) for group_id in ids]


def get_group_view(db: Session, group_id: str, actor_id: str, actor_is_admin: bool):
    if not actor_is_admin and not _is_member(db, group_id, actor_id):
        raise ForbiddenError("Not allowed")
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise NotFoundError("Group not found")
    members = (
        db.query(GroupMember, User)
        .join(User, User.id == GroupMember.user_id)
        .filter(GroupMember.group_id == group_id)
        .all()
    )
    return {
        "id": str(group.id),
        "name": group.name,
        "grade": group.grade,
        "year": group.year,
        "created_at": group.created_at.isoformat() if group.created_at else None,
        "members": [
            {"user_id": str(member.user_id), "email": user.email, "member_role": member.member_role}
            for member, user in members
        ],
    }
