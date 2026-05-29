from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.models.scheduled_scan import ScheduledScan
from app.models.project import Project
from app.models.user import User
from app.api.dependencies import get_current_user

router = APIRouter()


class ScheduleCreate(BaseModel):
    project_id: int
    interval_hours: int = 24
    notify_email: bool = True


class ScheduleResponse(BaseModel):
    id: int
    project_id: int
    interval_hours: int
    enabled: bool
    notify_email: bool
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=List[ScheduleResponse])
async def list_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ScheduledScan).filter(ScheduledScan.owner_id == current_user.id)
    )
    return result.scalars().all()


@router.post("/", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    data: ScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if data.interval_hours < 1:
        raise HTTPException(status_code=400, detail="interval_hours must be >= 1")

    proj = await db.execute(
        select(Project).filter(
            Project.id == data.project_id, Project.owner_id == current_user.id
        )
    )
    if not proj.scalars().first():
        raise HTTPException(status_code=404, detail="Project not found")

    now = datetime.now(timezone.utc)
    sched = ScheduledScan(
        project_id=data.project_id,
        owner_id=current_user.id,
        interval_hours=data.interval_hours,
        notify_email=data.notify_email,
        next_run_at=now,
    )
    db.add(sched)
    await db.commit()
    await db.refresh(sched)
    return sched


@router.post("/{schedule_id}/toggle", response_model=ScheduleResponse)
async def toggle_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ScheduledScan).filter(
            ScheduledScan.id == schedule_id,
            ScheduledScan.owner_id == current_user.id,
        )
    )
    sched = result.scalars().first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    sched.enabled = not sched.enabled
    await db.commit()
    await db.refresh(sched)
    return sched


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ScheduledScan).filter(
            ScheduledScan.id == schedule_id,
            ScheduledScan.owner_id == current_user.id,
        )
    )
    sched = result.scalars().first()
    if not sched:
        raise HTTPException(status_code=404, detail="Schedule not found")
    await db.delete(sched)
    await db.commit()
    return {"message": "Schedule deleted"}
