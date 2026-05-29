from app.core.database import Base
from app.models.user import User
from app.models.project import Project
from app.models.scan_result import ScanResult

# For Alembic to detect all models
__all__ = ["Base", "User", "Project", "ScanResult"]
