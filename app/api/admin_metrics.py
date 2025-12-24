from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_role
from app.schemas.metrics import MetricsHistoryResponse, MetricSampleDto
from app.services.metrics import latest_samples

router = APIRouter(prefix="/admin/metrics", tags=["admin-metrics"], dependencies=[Depends(require_role("ADMIN"))])


@router.get("/history", response_model=MetricsHistoryResponse)
def history(limit: int = Query(default=120, ge=1, le=500), db: Session = Depends(get_db)):
    samples = latest_samples(db, limit)
    items = [
        MetricSampleDto(
            captured_at=s.captured_at.isoformat(),
            heap_used_bytes=s.heap_used_bytes,
            heap_max_bytes=s.heap_max_bytes,
            system_memory_total_bytes=s.system_memory_total_bytes,
            system_memory_used_bytes=s.system_memory_used_bytes,
            disk_total_bytes=s.disk_total_bytes,
            disk_used_bytes=s.disk_used_bytes,
            process_cpu_load=s.process_cpu_load,
            system_cpu_load=s.system_cpu_load,
        )
        for s in samples
    ]
    return MetricsHistoryResponse(items=items)
