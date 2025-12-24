import psutil
import uuid
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.server_metric_sample import ServerMetricSample


def capture_metrics(db: Session) -> ServerMetricSample:
    process = psutil.Process()
    vm = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage(settings.metrics_disk_path)
    except Exception:
        disk = psutil.disk_usage("/")

    heap_used = process.memory_info().rss
    heap_max = vm.total

    sample = ServerMetricSample(
        id=uuid.uuid4(),
        captured_at=datetime.now(timezone.utc),
        heap_used_bytes=heap_used,
        heap_max_bytes=heap_max,
        system_memory_total_bytes=vm.total,
        system_memory_used_bytes=vm.total - vm.available,
        disk_total_bytes=disk.total,
        disk_used_bytes=disk.used,
        process_cpu_load=process.cpu_percent(interval=None) / 100.0,
        system_cpu_load=psutil.cpu_percent(interval=None) / 100.0,
    )
    db.add(sample)
    db.commit()
    db.refresh(sample)
    return sample


def latest_samples(db: Session, limit: int) -> list[ServerMetricSample]:
    items = (
        db.query(ServerMetricSample)
        .order_by(ServerMetricSample.captured_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(items))
