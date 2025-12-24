from sqlalchemy import Column, String, DateTime, BigInteger
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.db import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(UUID(as_uuid=True), primary_key=True)
    owner_user_id = Column(UUID(as_uuid=True))
    bucket = Column(String, nullable=False)
    storage_key = Column(String, nullable=False)
    filename = Column(String)
    description = Column(String)
    type = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    size_bytes = Column(BigInteger, nullable=False)
    sha256 = Column(String)
    access_policy = Column(String, nullable=False)
    status = Column(String, nullable=False)
    metadata_json = Column("metadata", JSONB)
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
