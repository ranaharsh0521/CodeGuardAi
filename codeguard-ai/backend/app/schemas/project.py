from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    team_id: Optional[int] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    repository_url: Optional[str] = None
    team_id: Optional[int] = None

class Project(ProjectBase):
    id: int
    owner_id: int
    team_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProjectResponse(Project):
    pass

class ProjectListResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    repository_url: Optional[str] = None
    team_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class GitHubRepository(BaseModel):
    id: int
    full_name: str
    name: str
    html_url: str
    clone_url: str
    private: bool
    default_branch: Optional[str] = None
    description: Optional[str] = None
    updated_at: Optional[datetime] = None
