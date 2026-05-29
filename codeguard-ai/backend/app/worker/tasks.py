"""Celery tasks for background scan execution."""

from __future__ import annotations

import asyncio

from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.run_scan_task", bind=True, max_retries=2)
def run_scan_task(self, scan_id: int) -> dict:
    from app.api.endpoints.tasks import run_scan_background

    try:
        asyncio.run(run_scan_background(scan_id))
        return {"scan_id": scan_id, "status": "ok"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
