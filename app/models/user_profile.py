from sqlalchemy import Column, String, Date, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.db import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    birth_date = Column(Date)
    gender = Column(String)
    phone = Column(String)
    school = Column(String)
    grade_level = Column(String)
    bio = Column(String)
    avatar_media_id = Column(UUID(as_uuid=True), ForeignKey("media_assets.id"))
    contact_json = Column(JSONB)
    metadata_json = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
