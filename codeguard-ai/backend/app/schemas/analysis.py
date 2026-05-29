from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Finding(BaseModel):
    tool: str
    rule_id: str
    message: str
    file_path: str
    line_number: int
    severity: str  # e.g., info, warning, error, critical
    code_snippet: Optional[str] = None
    ai_fix_suggestion: Optional[str] = None
    ai_explanation: Optional[str] = None

class AnalysisRequest(BaseModel):
    project_id: int
    repository_url: str
    commit_hash: Optional[str] = None

class AnalysisResponse(BaseModel):
    scan_id: int
    status: str
    message: str

class ScanDetails(BaseModel):
    scan_id: int
    status: str
    risk_score: int
    findings: List[Finding]
