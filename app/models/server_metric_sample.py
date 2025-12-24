from sqlalchemy import Column, DateTime, BigInteger, Float
from sqlalchemy.dialects.postgresql import UUID
from app.core.db import Base


class ServerMetricSample(Base):
    __tablename__ = "server_metric_samples"

    id = Column(UUID(as_uuid=True), primary_key=True)
    captured_at = Column(DateTime(timezone=True), nullable=False)
    heap_used_bytes = Column(BigInteger, nullable=False)
    heap_max_bytes = Column(BigInteger, nullable=False)
    system_memory_total_bytes = Column(BigInteger, nullable=False)
    system_memory_used_bytes = Column(BigInteger, nullable=False)
    disk_total_bytes = Column(BigInteger, nullable=False)
    disk_used_bytes = Column(BigInteger, nullable=False)
    process_cpu_load = Column(Float)
    system_cpu_load = Column(Float)
