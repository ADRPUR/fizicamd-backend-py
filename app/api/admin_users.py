import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role, hash_password
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.role import Role
from app.models.user_role import UserRole
from app.schemas.admin import (
    AdminUserResponse,
    AdminUserCreateRequest,
    AdminUserUpdateRequest,
    PagedResponse,
    AssignRoleRequest,
)
from app.services.media import delete_asset
from app.services.role_groups import ensure_membership

router = APIRouter(prefix="/admin/users", tags=["admin-users"], dependencies=[Depends(require_role("ADMIN"))])


def build_admin_response(db: Session, user: User) -> AdminUserResponse:
    roles = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    role_codes = [r[0] for r in roles]
    primary = role_codes[0] if role_codes else "STUDENT"
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        status=user.status,
        primary_role=primary,
        roles=role_codes,
        first_name=profile.first_name if profile else None,
        last_name=profile.last_name if profile else None,
        phone=profile.phone if profile else None,
        school=profile.school if profile else None,
        grade_level=profile.grade_level if profile else None,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        last_seen_at=user.last_seen_at.isoformat() if user.last_seen_at else None,
    )


@router.get("", response_model=PagedResponse)
def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100, alias="pageSize"),
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if search:
        query = query.filter(User.email.ilike(f"%{search}%"))
    total = query.count()
    items = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PagedResponse(
        items=[build_admin_response(db, user) for user in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=AdminUserResponse)
def create_user(payload: AdminUserCreateRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email.lower()).first():
        raise HTTPException(status_code=400, detail="User already exists")
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        status=payload.status or "ACTIVE",
        is_email_verified=False,
        created_at=now,
        updated_at=now,
        last_login_at=None,
        last_seen_at=None,
        deleted_at=None,
    )
    db.add(user)
    db.commit()

    profile = UserProfile(
        user_id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        phone=payload.phone,
        school=payload.school,
        grade_level=payload.grade_level,
        created_at=now,
        updated_at=now,
        contact_json={},
        metadata_json={},
    )
    db.add(profile)

    roles = payload.roles or ["STUDENT"]
    for role_code in roles:
        role = db.query(Role).filter(Role.code == role_code.upper()).first()
        if role:
            db.add(UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id, assigned_at=now))
            db.flush()
            ensure_membership(db, str(user.id), role.code)
    db.commit()

    return build_admin_response(db, user)


@router.put("/{user_id}", response_model=AdminUserResponse)
def update_user(user_id: str, payload: AdminUserUpdateRequest, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.email.lower() != payload.email.lower():
        raise HTTPException(status_code=400, detail="Email cannot be changed")
    user.status = payload.status or user.status
    user.updated_at = datetime.now(timezone.utc)

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        profile = UserProfile(user_id=user.id, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db.add(profile)
    profile.first_name = payload.first_name
    profile.last_name = payload.last_name
    profile.phone = payload.phone
    profile.school = payload.school
    profile.grade_level = payload.grade_level
    profile.updated_at = datetime.now(timezone.utc)

    desired = {r.upper() for r in (payload.roles or ["STUDENT"])}
    current = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    current_codes = {r[0] for r in current}
    for role_code in desired - current_codes:
        role = db.query(Role).filter(Role.code == role_code).first()
        if role:
            db.add(UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id, assigned_at=datetime.now(timezone.utc)))
            db.flush()
            ensure_membership(db, str(user.id), role.code)
    for role_code in current_codes - desired:
        role = db.query(Role).filter(Role.code == role_code).first()
        if role:
            db.query(UserRole).filter(UserRole.user_id == user.id, UserRole.role_id == role.id).delete()
    db.commit()

    return build_admin_response(db, user)


@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if profile and profile.avatar_media_id:
        delete_asset(db, profile.avatar_media_id)
    db.delete(user)
    db.commit()
    return None


@router.post("/{user_id}/roles", status_code=204)
def assign_role(user_id: str, payload: AssignRoleRequest, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.code == payload.role.upper()).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    existing = (
        db.query(UserRole)
        .filter(UserRole.user_id == user_id, UserRole.role_id == role.id)
        .first()
    )
    if not existing:
        db.add(UserRole(id=uuid.uuid4(), user_id=user_id, role_id=role.id, assigned_at=datetime.now(timezone.utc)))
        db.commit()
        ensure_membership(db, user_id, role.code)
    return None


@router.delete("/{user_id}/roles/{role_code}", status_code=204)
def remove_role(user_id: str, role_code: str, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.code == role_code.upper()).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    db.query(UserRole).filter(UserRole.user_id == user_id, UserRole.role_id == role.id).delete()
    db.commit()
    return None
