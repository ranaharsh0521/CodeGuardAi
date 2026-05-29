from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.analysis import Finding

class ScanCreate(BaseModel):
    project_id: int
    commit_hash: Optional[str] = None

class ScanResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    status: str
    progress: int = 0
    message: Optional[str] = None
    error_message: Optional[str] = None
    risk_score: int
    findings_count: int = 0
    commit_hash: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScanResultResponse(BaseModel):
    id: int
    project_id: int
    status: str
    progress: int = 0
    message: Optional[str] = None
    error_message: Optional[str] = None
    risk_score: int
    findings: List[Any] = []   # stored as raw JSON dicts in DB
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ScanStatusUpdate(BaseModel):
    status: str
    progress: int  # 0-100
    message: str
