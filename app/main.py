import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db, SessionLocal
from app.core.migrations import run_migrations
from app.core.security import decode_token
from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.api.auth import router as auth_router
from app.api.me import router as me_router
from app.api.admin_users import router as admin_users_router
from app.api.admin_metrics import router as admin_metrics_router
from app.api.resources_public import router as public_resources_router
from app.api.resources_teacher import router as teacher_resources_router
from app.api.resource_categories import router as resource_categories_router
from app.api.media import router as media_router
from app.api.public import router as public_router
from app.api.groups_admin import router as admin_groups_router
from app.api.groups_teacher import router as teacher_groups_router
from app.api.groups_student import router as student_groups_router
from app.services.metrics import capture_metrics
from app.ws.metrics import metrics_socket_manager
from app.services.role_groups import ensure_all_role_groups_exist

app = FastAPI(title="FizicaMD API")
logger = logging.getLogger("fizicamd")

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router, prefix="/api")
app.include_router(me_router, prefix="/api")
app.include_router(admin_users_router, prefix="/api")
app.include_router(admin_metrics_router, prefix="/api")
app.include_router(public_resources_router, prefix="/api")
app.include_router(teacher_resources_router, prefix="/api")
app.include_router(resource_categories_router, prefix="/api")
app.include_router(media_router, prefix="/api")
app.include_router(public_router, prefix="/api")
app.include_router(admin_groups_router, prefix="/api")
app.include_router(teacher_groups_router, prefix="/api")
app.include_router(student_groups_router, prefix="/api")


@app.exception_handler(NotFoundError)
def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=404, content={"message": str(exc)})


@app.exception_handler(BadRequestError)
def bad_request_handler(request: Request, exc: BadRequestError):
    return JSONResponse(status_code=400, content={"message": str(exc)})


@app.exception_handler(ForbiddenError)
def forbidden_handler(request: Request, exc: ForbiddenError):
    return JSONResponse(status_code=403, content={"message": str(exc)})


@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    message = "Validation failed"
    if exc.errors():
        first = exc.errors()[0]
        if "msg" in first:
            message = first["msg"]
    return JSONResponse(status_code=400, content={"message": message})


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"message": "Internal server error"})


@app.on_event("startup")
async def startup_event():
    run_migrations()
    db = SessionLocal()
    try:
        ensure_all_role_groups_exist(db)
    finally:
        db.close()
    asyncio.create_task(metrics_loop())


async def metrics_loop():
    while True:
        db = SessionLocal()
        try:
            sample = capture_metrics(db)
            payload = {
                "capturedAt": sample.captured_at.isoformat(),
                "heapUsedBytes": sample.heap_used_bytes,
                "heapMaxBytes": sample.heap_max_bytes,
                "systemMemoryTotalBytes": sample.system_memory_total_bytes,
                "systemMemoryUsedBytes": sample.system_memory_used_bytes,
                "diskTotalBytes": sample.disk_total_bytes,
                "diskUsedBytes": sample.disk_used_bytes,
                "processCpuLoad": sample.process_cpu_load,
                "systemCpuLoad": sample.system_cpu_load,
            }
            await metrics_socket_manager.broadcast(payload)
        finally:
            db.close()
        await asyncio.sleep(settings.metrics_sample_interval)


@app.websocket("/ws/metrics")
async def ws_metrics(ws: WebSocket):
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=1008)
        return
    try:
        claims = decode_token(token)
    except Exception:
        await ws.close(code=1008)
        return
    if claims.get("typ") != "access" or "ADMIN" not in (claims.get("roles") or []):
        await ws.close(code=1008)
        return

    await metrics_socket_manager.connect(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await metrics_socket_manager.disconnect(ws)
