import uuid
from datetime import datetime, timezone, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RegisterResponse, RefreshRequest
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.user_profile import UserProfile
from app.services.users import build_user_dto
from app.services.role_groups import ensure_user_memberships

router = APIRouter(prefix="/auth", tags=["auth"])


def parse_birth_date(value: str | None):
    if not value:
        return None
    return date.fromisoformat(value)


@router.post("/register", response_model=RegisterResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.confirm_password is not None and payload.password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password confirmation does not match")
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid.uuid4(),
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        status="ACTIVE",
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
        birth_date=parse_birth_date(payload.birth_date),
        gender=None,
        bio=None,
        contact_json={},
        metadata_json={},
        created_at=now,
        updated_at=now,
    )
    db.add(profile)

    role = db.query(Role).filter(Role.code == "STUDENT").first()
    if role:
        db.add(UserRole(id=uuid.uuid4(), user_id=user.id, role_id=role.id, assigned_at=now))
    db.commit()
    ensure_user_memberships(db, str(user.id))

    return RegisterResponse(user_id=str(user.id), email=user.email)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed")
    if user.status != "ACTIVE":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authentication failed")

    roles = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    role_codes = [r[0] for r in roles]
    access = create_access_token(str(user.id), user.email, role_codes)
    refresh = create_refresh_token(str(user.id))
    now = datetime.now(timezone.utc)
    user.last_login_at = now
    user.last_seen_at = now
    db.commit()

    return TokenResponse(
        access_token=access,
        refresh_token=refresh,
        expires_at=int((now + timedelta(seconds=settings.access_ttl_seconds)).timestamp()),
        user=build_user_dto(db, user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        claims = decode_token(payload.refresh_token)
        if claims.get("typ") != "refresh":
            raise HTTPException(status_code=401, detail="Authentication failed")
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")

    user = db.get(User, claims.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="Authentication failed")

    roles = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    role_codes = [r[0] for r in roles]
    access = create_access_token(str(user.id), user.email, role_codes)
    refresh_token = create_refresh_token(str(user.id))
    now = datetime.now(timezone.utc)
    return TokenResponse(
        access_token=access,
        refresh_token=refresh_token,
        expires_at=int((now + timedelta(seconds=settings.access_ttl_seconds)).timestamp()),
        user=build_user_dto(db, user),
    )


@router.post("/logout")
def logout():
    return {"status": "ok"}
