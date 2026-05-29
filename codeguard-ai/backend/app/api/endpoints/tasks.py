from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from fastapi import BackgroundTasks
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.scan_result import ScanResult
from app.services.scan_runner import ScanRunner


def dispatch_scan(scan_id: int, background_tasks: BackgroundTasks) -> None:
    if settings.USE_CELERY:
        try:
            from app.worker.tasks import run_scan_task
            run_scan_task.delay(scan_id)
            return
        except Exception as e:
            print(f"Celery dispatch failed, falling back: {e}")
    background_tasks.add_task(run_scan_background, scan_id=scan_id)


async def run_scan_background(scan_id: int) -> None:
    try:
        async with AsyncSessionLocal() as db:
            runner = ScanRunner()
            await asyncio.wait_for(
                runner.run_scan(scan_id=scan_id, db=db),
                timeout=settings.SCAN_TIMEOUT_SECONDS,
            )
    except asyncio.TimeoutError:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(ScanResult).filter(ScanResult.id == scan_id))
            scan = result.scalars().first()
            if scan and scan.status in {"pending", "running"}:
                scan.status = "failed"
                scan.progress = 100
                scan.message = "Scan timed out"
                scan.error_message = f"Scan exceeded {settings.SCAN_TIMEOUT_SECONDS} seconds"
                scan.completed_at = datetime.now(timezone.utc)
                await db.commit()
