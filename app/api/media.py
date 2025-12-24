from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user, require_any_role
from app.services.media import (
    save_avatar_upload,
    save_resource_upload,
    load_asset_path,
    build_asset_url,
    get_asset,
)

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/uploads/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = save_avatar_upload(db, file, str(user.id))
    return {"assetId": str(asset.id), "url": build_asset_url(asset.id)}


@router.post("/uploads/resource", dependencies=[Depends(require_any_role("TEACHER", "ADMIN"))])
def upload_resource(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    asset = save_resource_upload(db, file, str(user.id))
    return {"assetId": str(asset.id), "url": build_asset_url(asset.id)}


@router.get("/assets/{asset_id}/content")
def load_asset(asset_id: str, db: Session = Depends(get_db)):
    asset = get_asset(db, asset_id)
    path = load_asset_path(asset)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Fișierul nu mai există")
    headers = {}
    if asset.filename:
        headers["Content-Disposition"] = f'inline; filename="{asset.filename}"'
    return FileResponse(path, media_type=asset.content_type, headers=headers)
