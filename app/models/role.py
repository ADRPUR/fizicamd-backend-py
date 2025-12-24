from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True)
    code = Column(String, nullable=False, unique=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False)
