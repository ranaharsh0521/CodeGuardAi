from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_

from app.core.database import get_db
from app.models.scan_result import ScanResult
from app.models.project import Project
from app.models.team import TeamMember
from app.models.user import User
from app.schemas.analysis import ScanDetails, Finding
from app.api.dependencies import get_current_user
from app.services.report_generator import ReportGenerator

router = APIRouter()


def _accessible_project_filter(user_id: int):
    team_ids_q = select(TeamMember.team_id).filter(TeamMember.user_id == user_id)
    return or_(
        Project.owner_id == user_id,
        Project.team_id.in_(team_ids_q),
    )

@router.get("/{scan_id}/pdf")
async def generate_pdf_report(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate PDF report for a scan"""
    
    # Get scan with ownership check
    result = await db.execute(
        select(ScanResult).join(Project).filter(
            ScanResult.id == scan_id,
            _accessible_project_filter(current_user.id),
        )
    )
    scan = result.scalars().first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    try:
        # Convert scan to ScanDetails format
        findings = [Finding(**f) for f in scan.findings] if scan.findings else []
        scan_details = ScanDetails(
            scan_id=scan.id,
            status=scan.status,
            risk_score=scan.risk_score,
            findings=findings
        )
        
        # Generate PDF
        report_generator = ReportGenerator()
        pdf_path = report_generator.generate_pdf(scan_details)
        
        # Return PDF file
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"codeguard_scan_{scan_id}_report.pdf"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@router.get("/{scan_id}/json")
async def get_json_report(
    scan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get JSON format report for a scan"""
    
    # Get scan with ownership check
    result = await db.execute(
        select(ScanResult).join(Project).filter(
            ScanResult.id == scan_id,
            _accessible_project_filter(current_user.id),
        )
    )
    scan = result.scalars().first()
    
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    # Get project info
    project_result = await db.execute(
        select(Project).filter(Project.id == scan.project_id)
    )
    project = project_result.scalars().first()
    
    return {
        "scan_id": scan.id,
        "project_name": project.name if project else "Unknown",
        "status": scan.status,
        "risk_score": scan.risk_score,
        "created_at": scan.created_at.isoformat(),
        "completed_at": scan.completed_at.isoformat() if scan.completed_at else None,
        "findings": scan.findings or [],
        "summary": {
            "total_findings": len(scan.findings) if scan.findings else 0,
            "critical": len([f for f in scan.findings if f.get("severity") == "critical"]) if scan.findings else 0,
            "high": len([f for f in scan.findings if f.get("severity") == "error"]) if scan.findings else 0,
            "medium": len([f for f in scan.findings if f.get("severity") == "warning"]) if scan.findings else 0,
            "low": len([f for f in scan.findings if f.get("severity") == "info"]) if scan.findings else 0,
        }
    }
