from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timezone
from typing import List, Optional, Literal, Any
from pydantic import BaseModel, Field

from app.api.endpoints.tasks import dispatch_scan

from app.core.database import get_db
from app.models.scan_result import ScanResult
from app.models.project import Project
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.scan import ScanCreate, ScanResponse, ScanResultResponse
from app.api.dependencies import get_current_user

router = APIRouter()


class FindingWorkflowUpdate(BaseModel):
    status: Literal["open", "resolved", "ignored", "false_positive"]
    comment: Optional[str] = Field(default=None, max_length=500)
    assignee: Optional[str] = Field(default=None, max_length=120)


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


def _finding_key(finding: dict[str, Any]) -> str:
    normalized_path = str(finding.get("file_path", "")).replace("\\", "/").strip()
    path_parts = [part for part in normalized_path.split("/") if part]
    workdir_index = next(
        (index for index, part in enumerate(path_parts) if part.startswith("work_")),
        None,
    )
    if workdir_index is not None and workdir_index + 1 < len(path_parts):
        normalized_path = "/".join(path_parts[workdir_index + 1 :])

    return "|".join(
        str(value).strip()
        for value in (
            finding.get("rule_id", ""),
            normalized_path,
            finding.get("message", ""),
        )
    )


async def _get_accessible_scan(scan_id: int, db: AsyncSession, user_id: int) -> ScanResult | None:
    result = await db.execute(
        select(ScanResult).join(Project).filter(
            ScanResult.id == scan_id,
            _accessible_project_filter(user_id),
        )
    )
    return result.scalars().first()

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


@router.put("/{scan_id}/findings/{finding_index}/workflow")
async def update_finding_workflow(
    scan_id: int,
    finding_index: int,
    data: FindingWorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update triage state for one finding in a scan result."""
    scan = await _get_accessible_scan(scan_id, db, current_user.id)
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    findings = list(scan.findings or [])
    if finding_index < 0 or finding_index >= len(findings):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        )

    finding = dict(findings[finding_index])
    finding["workflow_status"] = data.status
    finding["workflow_comment"] = data.comment
    finding["workflow_assignee"] = data.assignee
    finding["workflow_updated_at"] = datetime.now(timezone.utc).isoformat()
    findings[finding_index] = finding

    scan.findings = findings
    flag_modified(scan, "findings")
    await db.commit()

    return {
        "scan_id": scan.id,
        "finding_index": finding_index,
        "finding": finding,
    }


@router.get("/{scan_id}/comparison")
async def compare_scan(
    scan_id: int,
    base_scan_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compare a scan with a chosen or previous completed scan for the project."""
    current = await _get_accessible_scan(scan_id, db, current_user.id)
    if not current:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found",
        )

    base = None
    if base_scan_id is not None:
        base = await _get_accessible_scan(base_scan_id, db, current_user.id)
        if not base or base.project_id != current.project_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Base scan not found for this project",
            )
    else:
        result = await db.execute(
            select(ScanResult)
            .filter(
                ScanResult.project_id == current.project_id,
                ScanResult.id != current.id,
                ScanResult.status == "completed",
                ScanResult.created_at <= current.created_at,
            )
            .order_by(ScanResult.created_at.desc())
        )
        base = result.scalars().first()

    current_findings = [f for f in (current.findings or []) if isinstance(f, dict)]
    base_findings = [f for f in (base.findings or []) if isinstance(f, dict)] if base else []

    current_map = {_finding_key(f): f for f in current_findings}
    base_map = {_finding_key(f): f for f in base_findings}
    current_keys = set(current_map)
    base_keys = set(base_map)

    new_keys = current_keys - base_keys
    resolved_keys = base_keys - current_keys
    unchanged_keys = current_keys & base_keys

    return {
        "current_scan_id": current.id,
        "base_scan_id": base.id if base else None,
        "project_id": current.project_id,
        "current_risk_score": current.risk_score or 0,
        "base_risk_score": base.risk_score if base else None,
        "risk_delta": (current.risk_score or 0) - (base.risk_score or 0) if base else None,
        "current_findings_count": len(current_findings),
        "base_findings_count": len(base_findings),
        "new_findings_count": len(new_keys),
        "resolved_findings_count": len(resolved_keys),
        "unchanged_findings_count": len(unchanged_keys),
        "new_findings": [current_map[key] for key in sorted(new_keys)],
        "resolved_findings": [base_map[key] for key in sorted(resolved_keys)],
    }

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
