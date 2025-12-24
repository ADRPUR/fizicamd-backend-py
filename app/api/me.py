import uuid
from datetime import datetime, timezone, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user, hash_password, verify_password
from app.models.user import User
from app.models.user_profile import UserProfile
from app.schemas.profile import ProfileUpdateRequest, ChangePasswordRequest
from app.services.media import delete_asset
from app.services.users import build_user_dto

router = APIRouter(prefix="/me", tags=["me"])


def parse_date(value: str | None):
    if not value:
        return None
    return date.fromisoformat(value)


@router.get("")
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    dto = build_user_dto(db, user)
    if profile:
        dto.profile.birth_date = profile.birth_date.isoformat() if profile.birth_date else None
    return {"user": dto}


@router.get("/profile")
def profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return me(user, db)


@router.put("/profile")
def update_profile(payload: ProfileUpdateRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    now = datetime.now(timezone.utc)
    if not profile:
        profile = UserProfile(user_id=user.id, created_at=now, updated_at=now, contact_json={}, metadata_json={})
        db.add(profile)
    profile.first_name = payload.first_name
    profile.last_name = payload.last_name
    profile.birth_date = parse_date(payload.birth_date)
    profile.gender = payload.gender
    profile.phone = payload.phone
    profile.school = payload.school
    profile.grade_level = payload.grade_level
    profile.bio = payload.bio
    profile.updated_at = now
    db.commit()
    return {"user": build_user_dto(db, user)}


@router.delete("")
def delete_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if profile and profile.avatar_media_id:
        delete_asset(db, profile.avatar_media_id)
    db.delete(user)
    db.commit()
    return None


@router.put("/password")
def change_password(payload: ChangePasswordRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=400, detail="Password confirmation does not match")
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Authentication failed")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return None


@router.post("/ping")
def ping(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return None
