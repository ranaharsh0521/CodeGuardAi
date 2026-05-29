"""APScheduler-based scheduled scan runner."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import or_
from sqlalchemy.future import select

from app.core.database import AsyncSessionLocal
from app.models.scheduled_scan import ScheduledScan
from app.models.project import Project
from app.models.scan_result import ScanResult
from app.api.endpoints.tasks import run_scan_background

scheduler = AsyncIOScheduler()


async def run_due_scheduled_scans() -> None:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(ScheduledScan).filter(
                ScheduledScan.enabled == True,
                or_(ScheduledScan.next_run_at.is_(None), ScheduledScan.next_run_at <= now),
            )
        )
        schedules = result.scalars().all()

        for sched in schedules:
            proj_res = await db.execute(select(Project).filter(Project.id == sched.project_id))
            project = proj_res.scalars().first()
            if not project:
                continue

            db_scan = ScanResult(
                project_id=sched.project_id,
                status="pending",
                risk_score=0,
                findings=[],
            )
            db.add(db_scan)
            sched.last_run_at = now
            sched.next_run_at = now + timedelta(hours=sched.interval_hours)
            await db.commit()
            await db.refresh(db_scan)

            await run_scan_background(db_scan.id)


def start_scheduler() -> None:
    if not scheduler.running:
        scheduler.add_job(
            run_due_scheduled_scans,
            "interval",
            minutes=1,
            id="scheduled_scans",
            replace_existing=True,
        )
        scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
