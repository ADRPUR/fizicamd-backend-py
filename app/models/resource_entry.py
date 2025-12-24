from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.db import Base


class ResourceEntry(Base):
    __tablename__ = "resource_entries"

    id = Column(UUID(as_uuid=True), primary_key=True)
    category_code = Column(String, nullable=False)
    author_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String, nullable=False)
    slug = Column(String, nullable=False, unique=True)
    summary = Column(String, nullable=False)
    avatar_media_id = Column(UUID(as_uuid=True))
    content = Column(JSONB, nullable=False)
    tags = Column(JSONB, nullable=False)
    status = Column(String, nullable=False)
    published_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
