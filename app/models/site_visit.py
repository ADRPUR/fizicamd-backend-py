from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base


class SiteVisit(Base):
    __tablename__ = "site_visits"

    id = Column(UUID(as_uuid=True), primary_key=True)
    ip_address = Column(String)
    user_agent = Column(String)
    path = Column(String)
    referrer = Column(String)
    created_at = Column(DateTime(timezone=True), nullable=False)
