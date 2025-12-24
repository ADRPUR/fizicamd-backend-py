from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole
from app.models.user_profile import UserProfile
from app.schemas.auth import UserDto, UserProfileDto
from app.services.media import build_asset_url


def build_user_dto(db: Session, user: User) -> UserDto:
    roles = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user.id)
        .all()
    )
    role_codes = [r[0] for r in roles]
    primary = role_codes[0] if role_codes else "STUDENT"
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    profile_dto = None
    if profile:
        profile_dto = UserProfileDto(
            first_name=profile.first_name,
            last_name=profile.last_name,
            phone=profile.phone,
            school=profile.school,
            grade_level=profile.grade_level,
            birth_date=profile.birth_date.isoformat() if profile.birth_date else None,
            gender=profile.gender,
            bio=profile.bio,
            avatar_url=build_asset_url(profile.avatar_media_id) if profile.avatar_media_id else None,
        )
    return UserDto(
        id=str(user.id),
        email=user.email,
        status=user.status,
        role=primary,
        roles=role_codes,
        profile=profile_dto,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )


def get_user_roles(db: Session, user_id: str) -> set[str]:
    roles = (
        db.query(Role.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return {r[0] for r in roles}


def has_role(db: Session, user_id: str, role: str) -> bool:
    return role in get_user_roles(db, user_id)
