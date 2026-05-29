from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class ScanResult(Base):
    __tablename__ = "scan_results"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    commit_hash = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    progress = Column(Integer, default=0)
    message = Column(String, nullable=True)
    error_message = Column(String, nullable=True)
    risk_score = Column(Integer, default=0)
    findings = Column(JSON, default=list)
    quality_gate_result = Column(JSON, nullable=True)  # {passed, gates, summary}
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    project = relationship("Project", backref="scan_results")
