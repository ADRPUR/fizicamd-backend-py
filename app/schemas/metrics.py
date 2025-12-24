from pydantic import BaseModel
from typing import List, Optional


class MetricSampleDto(BaseModel):
    captured_at: str
    heap_used_bytes: int
    heap_max_bytes: int
    system_memory_total_bytes: int
    system_memory_used_bytes: int
    disk_total_bytes: int
    disk_used_bytes: int
    process_cpu_load: Optional[float] = None
    system_cpu_load: Optional[float] = None


class MetricsHistoryResponse(BaseModel):
    items: List[MetricSampleDto]
