from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from datetime import datetime, timezone
from typing import List

from app.api.endpoints.tasks import dispatch_scan

from app.core.database import get_db
from app.models.scan_result import ScanResult
from app.models.project import Project
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultResponse
from app.api.dependencies import get_current_user

router = APIRouter()


def _mark_stale_scan_failed(scan: ScanResult, max_age_seconds: int = 600) -> bool:
    if scan.status not in {"pending", "running"} or not scan.created_at:
        return False
    created_at = scan.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
    if age_seconds < max_age_seconds:
        return False
    scan.status = "failed"
    scan.progress = 100
    scan.message = "Scan interrupted"
    scan.error_message = "Scan took too long or the server restarted. Start a new scan."
    scan.completed_at = datetime.now(timezone.utc)
    return True


def _accessible_project_filter(user_id: int):
    team_ids_q = select(TeamMember.team_id).filter(TeamMember.user_id == user_id)
    return or_(
        Project.owner_id == user_id,
        Project.team_id.in_(team_ids_q),
    )

@router.post("/", response_model=ScanResponse)
async def trigger_scan(
    scan_data: ScanCreate,
    background_tasks: BackgroundTasks,

    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Trigger a new security scan on a project"""
    # Verify project exists and belongs to user
    result = await db.execute(
        select(Project).filter(
            Project.id == scan_data.project_id,
            _accessible_project_filter(current_user.id),
        )
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Capture project name now — after db.commit() SQLAlchemy may expire the
    # in-session object and a lazy reload could return None on some backends.
    project_name = project.name

    # Create scan record
    db_scan = ScanResult(
        project_id=scan_data.project_id,
        commit_hash=scan_data.commit_hash,
        status="pending",
        progress=0,
        message="Queued",
        error_message=None,
        risk_score=0,
        findings=[]
    )

    db.add(db_scan)
    await db.commit()
    await db.refresh(db_scan)

    # Background trigger (dev-friendly; Celery can be wired later)
    # NOTE: do NOT pass `db` — the request session is closed before the task runs.
    dispatch_scan(db_scan.id, background_tasks)

    # Build response dict explicitly — ScanResponse requires `findings_count` and
    # `project_name` which are computed fields not present on the ORM object.
    return {
        "id": db_scan.id,
        "project_id": db_scan.project_id,
        "project_name": project_name,
        "status": db_scan.status,
        "progress": db_scan.progress or 0,
        "message": db_scan.message,
        "error_message": db_scan.error_message,
        "risk_score": db_scan.risk_score or 0,
        "findings_count": 0,
        "commit_hash": db_scan.commit_hash,
        "created_at": db_scan.created_at,
        "completed_at": db_scan.completed_at,
    }

@router.get("/", response_model=List[ScanResponse])
async def list_scans(
    project_id: int = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all scans for a project or all projects"""
    if project_id:
        # Verify project exists and belongs to user
        result = await db.execute(
            select(Project).filter(
                Project.id == project_id,
                _accessible_project_filter(current_user.id),
            )
        )
        project = result.scalars().first()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Get scans for specific project
        result = await db.execute(
            select(ScanResult).filter(
                ScanResult.project_id == project_id
            ).order_by(ScanResult.created_at.desc())
        )
    else:
        # Get scans for all user projects
        result = await db.execute(
            select(ScanResult).join(Project).filter(
                _accessible_project_filter(current_user.id)
            ).order_by(ScanResult.created_at.desc())
        )
    
    scans = result.scalars().all()

    # Resolve project names for list view
    project_ids = {s.project_id for s in scans}
    projects_map = {}
    if project_ids:
        proj_result = await db.execute(
            select(Project).filter(Project.id.in_(project_ids))
        )
        for p in proj_result.scalars().all():
            projects_map[p.id] = p.name

    return [
        {
            "id": s.id,
            "project_id": s.project_id,
            "project_name": projects_map.get(s.project_id, f"Project {s.project_id}"),
            "status": s.status,
            "progress": s.progress or 0,
            "message": s.message,
            "error_message": s.error_message,
            "risk_score": s.risk_score,
            "findings_count": len(s.findings) if s.findings else 0,
            "commit_hash": s.commit_hash,
            "created_at": s.created_at,
            "completed_at": s.completed_at,
        }
        for s in scans
    ]

@router.get("/{scan_id}", response_model=ScanResultResponse)
async def get_scan_result(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed scan results"""
    result = await db.execute(
        select(ScanResult).join(Project).filter(
            ScanResult.id == scan_id,
            _accessible_project_filter(current_user.id),
        )
    )
    scan = result.scalars().first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    if _mark_stale_scan_failed(scan):
        await db.commit()
    
    return scan

@router.get("/{scan_id}/status")
async def get_scan_status(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get scan status for real-time updates"""
    result = await db.execute(
        select(ScanResult).join(Project).filter(
            ScanResult.id == scan_id,
            _accessible_project_filter(current_user.id),
        )
    )
    scan = result.scalars().first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )

    if _mark_stale_scan_failed(scan):
        await db.commit()
    
    return {
        "scan_id": scan.id,
        "status": scan.status,
        "progress": scan.progress or 0,
        "message": scan.message,
        "error_message": scan.error_message,
        "risk_score": scan.risk_score,
        "findings_count": len(scan.findings) if scan.findings else 0,
        "created_at": scan.created_at,
        "completed_at": scan.completed_at
    }

@router.delete("/{scan_id}")
async def delete_scan(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a scan result"""
    result = await db.execute(
        select(ScanResult).join(Project).filter(
            ScanResult.id == scan_id,
            _accessible_project_filter(current_user.id),
        )
    )
    scan = result.scalars().first()
    
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
    
    await db.delete(scan)
    await db.commit()
    
    return {"message": "Scan deleted successfully"}
