import asyncio
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base, run_migrations
from app.api.endpoints import auth, projects, scans, users, chat, upload, reports, teams, schedules
from app.services.scheduler_service import start_scheduler, stop_scheduler
from app.services.scan_events import register_listener, unregister_listener, forward_redis_to_queue

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await run_migrations(conn)
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered Code Security & Bug Analyzer",
    version="1.1.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Authorization", "Accept", "Origin", "X-Requested-With"],
    expose_headers=["Content-Length", "X-Request-ID"],
    max_age=600,
)


@app.get("/health")
def health_check():
    dev_oauth_active = (
        settings.DEV_OAUTH_FALLBACK
        and ("localhost" in settings.BACKEND_URL or "127.0.0.1" in settings.BACKEND_URL)
        and ("localhost" in settings.FRONTEND_URL or "127.0.0.1" in settings.FRONTEND_URL)
    )
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": "1.1.0",
        "features": {
            "github_oauth": bool(settings.GITHUB_CLIENT_ID) or dev_oauth_active,
            "google_oauth": bool(settings.GOOGLE_CLIENT_ID) or dev_oauth_active,
            "celery": settings.USE_CELERY,
            "email": bool(settings.SMTP_HOST),
            "scheduler": True,
            "demo_findings": settings.ENABLE_DEMO_FINDINGS,
            "dev_oauth_fallback": dev_oauth_active,
        },
    }

app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(projects.router, prefix=f"{settings.API_V1_STR}/projects", tags=["Projects"])
app.include_router(scans.router, prefix=f"{settings.API_V1_STR}/scans", tags=["Scans"])
app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["Chat"])
app.include_router(upload.router, prefix=f"{settings.API_V1_STR}/upload", tags=["Upload"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(teams.router, prefix=f"{settings.API_V1_STR}/teams", tags=["Teams"])
app.include_router(schedules.router, prefix=f"{settings.API_V1_STR}/schedules", tags=["Scheduled Scans"])


@app.websocket("/ws/scan-progress")
async def websocket_scan_progress(
    websocket: WebSocket,
    scan_id: int = Query(..., description="Scan ID to subscribe to"),
):
    """Real-time scan progress via Redis pub/sub + in-memory events."""
    await websocket.accept()
    queue = register_listener(scan_id)
    redis_task = asyncio.create_task(forward_redis_to_queue(scan_id, queue))
    try:
        while True:
            message = await queue.get()
            await websocket.send_text(message)
            try:
                data = json.loads(message)
                if data.get("status") in ("completed", "failed"):
                    break
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        redis_task.cancel()
        unregister_listener(scan_id, queue)
