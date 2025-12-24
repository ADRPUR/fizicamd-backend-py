import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.errors import BadRequestError, NotFoundError
from app.models.media_asset import MediaAsset
from app.models.user_profile import UserProfile

USERS_BUCKET = "users"
RESOURCES_BUCKET = "resources"

BASE_DIR = Path(settings.media_storage_path)
BASE_DIR.mkdir(parents=True, exist_ok=True)


def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            sha.update(chunk)
    return sha.hexdigest()


def build_asset_url(asset_id: uuid.UUID) -> str:
    return f"/media/assets/{asset_id}/content"


def _bucket_path(bucket: str) -> Path:
    path = BASE_DIR / bucket
    path.mkdir(parents=True, exist_ok=True)
    return path


def _store_file(bucket: str, storage_key: str, content: bytes) -> Path:
    target = _bucket_path(bucket) / storage_key
    with target.open("wb") as out:
        out.write(content)
    return target


def _ensure_non_empty(file) -> bytes:
    content = file.file.read()
    if not content:
        raise BadRequestError("Fișierul este gol.")
    return content


def _resolve_media_type(content_type: str) -> str:
    if content_type.startswith("image/"):
        return "IMAGE"
    if content_type.lower() == "application/pdf":
        return "DOCUMENT"
    return "OTHER"


def save_avatar_upload(db: Session, file, owner_user_id: str) -> MediaAsset:
    content_type = file.content_type or "application/octet-stream"
    content = _ensure_non_empty(file)
    asset_id = uuid.uuid4()
    filename = file.filename or "upload"
    storage_key = str(asset_id)
    target = _store_file(USERS_BUCKET, storage_key, content)

    asset = MediaAsset(
        id=asset_id,
        owner_user_id=owner_user_id,
        bucket=USERS_BUCKET,
        storage_key=storage_key,
        filename=filename,
        description=None,
        type="AVATAR",
        content_type=content_type,
        size_bytes=target.stat().st_size,
        sha256=_hash_file(target),
        access_policy="PRIVATE",
        status="READY",
        metadata_json={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    profile = db.query(UserProfile).filter(UserProfile.user_id == owner_user_id).first()
    if not profile:
        profile = UserProfile(
            user_id=owner_user_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            contact_json={},
            metadata_json={},
        )
        db.add(profile)
    previous = profile.avatar_media_id
    profile.avatar_media_id = asset.id
    profile.updated_at = datetime.now(timezone.utc)
    db.commit()

    if previous:
        delete_asset(db, previous)

    return asset


def save_resource_upload(db: Session, file, owner_user_id: str) -> MediaAsset:
    content_type = file.content_type or "application/octet-stream"
    content = _ensure_non_empty(file)
    asset_id = uuid.uuid4()
    filename = file.filename or "upload"
    storage_key = str(asset_id)
    target = _store_file(RESOURCES_BUCKET, storage_key, content)

    asset = MediaAsset(
        id=asset_id,
        owner_user_id=owner_user_id,
        bucket=RESOURCES_BUCKET,
        storage_key=storage_key,
        filename=filename,
        description=None,
        type=_resolve_media_type(content_type),
        content_type=content_type,
        size_bytes=target.stat().st_size,
        sha256=_hash_file(target),
        access_policy="PRIVATE",
        status="READY",
        metadata_json={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


def load_asset_path(asset: MediaAsset) -> Path:
    return _bucket_path(asset.bucket) / asset.storage_key


def delete_asset(db: Session, asset_id: uuid.UUID):
    asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
    if not asset:
        return
    path = load_asset_path(asset)
    db.delete(asset)
    db.commit()
    if path.exists():
        path.unlink()


def get_asset(db: Session, asset_id: str) -> MediaAsset:
    asset = db.query(MediaAsset).filter(MediaAsset.id == asset_id).first()
    if not asset:
        raise NotFoundError("Media negăsită")
    return asset
