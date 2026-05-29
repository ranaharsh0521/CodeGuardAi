from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import tempfile
import os

from app.core.database import get_db
from app.models.project import Project
from app.models.scan_result import ScanResult
from app.models.user import User
from app.schemas.scan import ScanResponse
from app.api.dependencies import get_current_user
from app.services.analyzer_service import AnalyzerService

router = APIRouter()

SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h",
    ".php", ".rb", ".go", ".rs", ".kt", ".scala", ".cs", ".swift",
    ".sql", ".sh", ".bash", ".yaml", ".yml", ".json", ".xml",
}
MAX_FILES = 50
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024


def _safe_filename(filename: str) -> str:
    normalized = os.path.basename(filename.replace("\\", "/"))
    if not normalized or normalized in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return normalized


async def _save_upload(file: UploadFile, destination: str) -> None:
    written = 0
    with open(destination, "wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=413,
                    detail=f"{file.filename} exceeds the 10 MB file size limit",
                )
            buffer.write(chunk)

@router.post("/upload-scan", response_model=ScanResponse)
async def upload_and_scan(
    files: List[UploadFile] = File(...),
    project_name: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload files and run immediate security scan"""
    if not files:
        raise HTTPException(status_code=400, detail="At least one file is required")
    if len(files) > MAX_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_FILES} files allowed")

    safe_files = []
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="All uploaded files must have names")
        filename = _safe_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        if ext not in SUPPORTED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext or 'none'}")
        safe_files.append((file, filename))
    
    # Create temporary project if none specified
    if not project_name:
        project_name = f"Upload Scan {len(files)} files"
    
    # Create project
    db_project = Project(
        name=project_name,
        description=f"Direct upload scan with {len(files)} files",
        owner_id=current_user.id
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    
    # Create scan record
    db_scan = ScanResult(
        project_id=db_project.id,
        status="running",
        progress=10,
        message="Uploading files",
        error_message=None,
        risk_score=0,
        findings=[]
    )
    db.add(db_scan)
    await db.commit()
    await db.refresh(db_scan)
    
    try:
        # Create temporary directory for uploaded files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded files
            for file, filename in safe_files:
                file_path = os.path.join(temp_dir, filename)
                await _save_upload(file, file_path)
            
            # Run analysis
            analyzer = AnalyzerService()
            findings = analyzer.run_full_analysis(temp_dir)
            risk_score = analyzer.calculate_risk_score(findings)
            
            # Update scan with results
            db_scan.findings = [f.model_dump() for f in findings]
            db_scan.risk_score = risk_score
            db_scan.status = "completed"
            db_scan.progress = 100
            db_scan.message = "Scan complete"
            db_scan.error_message = None
            
            await db.commit()
            await db.refresh(db_scan)
            
    except Exception as e:
        db_scan.status = "failed"
        db_scan.progress = 100
        db_scan.message = "Scan failed"
        db_scan.error_message = str(e)
        await db.commit()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    
    return db_scan

@router.get("/supported-extensions")
async def get_supported_extensions():
    """Get list of supported file extensions for upload"""
    return {
        "extensions": [
            *sorted(SUPPORTED_EXTENSIONS)
        ],
        "max_file_size_mb": 10,
        "max_files": 50
    }
