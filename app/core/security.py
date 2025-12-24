from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from passlib.hash import argon2
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.user import User
from app.models.role import Role
from app.models.user_role import UserRole

security = HTTPBearer()


def hash_password(raw: str) -> str:
    return argon2.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return argon2.verify(raw, hashed)
    except Exception:
        return False


def create_access_token(user_id: str, email: str, roles: list[str], ttl_seconds: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=ttl_seconds or settings.access_ttl_seconds)
    payload = {
        "iss": settings.jwt_issuer,
        "sub": user_id,
        "typ": "access",
        "email": email,
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def create_refresh_token(user_id: str, ttl_seconds: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(seconds=ttl_seconds or settings.refresh_ttl_seconds)
    payload = {
        "iss": settings.jwt_issuer,
        "sub": user_id,
        "typ": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=["HS256"], issuer=settings.jwt_issuer)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = creds.credentials
    try:
        claims = decode_token(token)
        if claims.get("typ") != "access":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        user_id = claims.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user


def require_role(role: str):
    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        roles = (
            db.query(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
        role_codes = {r[0] for r in roles}
        if role not in role_codes:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return user

    return checker


def require_any_role(*roles_required: str):
    def checker(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        roles = (
            db.query(Role.code)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .all()
        )
        role_codes = {r[0] for r in roles}
        if not any(role in role_codes for role in roles_required):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
        return user

    return checker
