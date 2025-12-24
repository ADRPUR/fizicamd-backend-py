from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base


class ResourceCategory(Base):
    __tablename__ = "resource_categories"

    id = Column(UUID(as_uuid=True), primary_key=True)
    code = Column(String, nullable=False, unique=True)
    label = Column(String, nullable=False)
    group_label = Column(String, nullable=False)
    sort_order = Column(Integer, nullable=False, default=0)
    group_order = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
