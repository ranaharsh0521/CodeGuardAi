import httpx
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.core.database import get_db
from app.models.project import Project
from app.models.user import User
from app.models.team import TeamMember
from sqlalchemy import or_
from app.schemas.project import (
    GitHubRepository,
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
)
from app.api.dependencies import get_current_user

router = APIRouter()


async def _ensure_team_admin(team_id: int, user_id: int, db: AsyncSession) -> None:
    result = await db.execute(
        select(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
            TeamMember.role.in_(["owner", "admin"]),
        )
    )
    if not result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owners or admins can assign projects to this team",
        )

@router.get("/", response_model=List[ProjectListResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List projects owned by user or shared via team membership."""
    team_ids_q = select(TeamMember.team_id).filter(TeamMember.user_id == current_user.id)
    result = await db.execute(
        select(Project).filter(
            or_(
                Project.owner_id == current_user.id,
                Project.team_id.in_(team_ids_q),
            )
        )
    )
    return result.scalars().all()

@router.post("/", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    if project_data.team_id is not None:
        await _ensure_team_admin(project_data.team_id, current_user.id, db)

    db_project = Project(
        name=project_data.name,
        description=project_data.description,
        repository_url=project_data.repository_url,
        owner_id=current_user.id,
        team_id=project_data.team_id,
    )
    
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    
    return db_project

@router.get("/github/repositories", response_model=List[GitHubRepository])
async def list_github_repositories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List GitHub repositories available to the connected GitHub account."""
    if not current_user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connect GitHub first to import repositories",
        )

    repos: list[dict] = []
    page = 1
    headers = {
        "Authorization": f"Bearer {current_user.github_access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            while page <= 5:
                response = await client.get(
                    "https://api.github.com/user/repos",
                    headers=headers,
                    params={
                        "visibility": "all",
                        "affiliation": "owner,collaborator,organization_member",
                        "sort": "updated",
                        "per_page": 100,
                        "page": page,
                    },
                )
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="GitHub connection expired. Please reconnect GitHub.",
                    )
                response.raise_for_status()

                batch = response.json()
                if not batch:
                    break
                repos.extend(batch)
                if len(batch) < 100:
                    break
                page += 1
    except HTTPException:
        raise
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch GitHub repositories: {exc}",
        ) from exc

    return [
        GitHubRepository(
            id=repo["id"],
            full_name=repo["full_name"],
            name=repo["name"],
            html_url=repo["html_url"],
            clone_url=repo["clone_url"],
            private=repo["private"],
            default_branch=repo.get("default_branch"),
            description=repo.get("description"),
            updated_at=repo.get("updated_at"),
        )
        for repo in repos
    ]

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific project (owner or team member)"""
    team_ids_q = select(TeamMember.team_id).filter(TeamMember.user_id == current_user.id)
    result = await db.execute(
        select(Project).filter(
            Project.id == project_id,
            or_(
                Project.owner_id == current_user.id,
                Project.team_id.in_(team_ids_q),
            ),
        )
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    result = await db.execute(
        select(Project).filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update fields if provided
    if project_data.name is not None:
        project.name = project_data.name
    if project_data.description is not None:
        project.description = project_data.description
    if project_data.repository_url is not None:
        project.repository_url = project_data.repository_url
    if project_data.team_id is not None:
        await _ensure_team_admin(project_data.team_id, current_user.id, db)
        project.team_id = project_data.team_id
    
    await db.commit()
    await db.refresh(project)
    
    return project

@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a project"""
    result = await db.execute(
        select(Project).filter(
            Project.id == project_id,
            Project.owner_id == current_user.id
        )
    )
    project = result.scalars().first()
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}
