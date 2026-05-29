from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from app.core.database import get_db
from app.models.team import Team, TeamMember
from app.models.user import User
from app.api.dependencies import get_current_user
from app.services.email_service import EmailService
from pydantic import BaseModel, EmailStr
from datetime import datetime

router = APIRouter()


class TeamCreate(BaseModel):
    name: str


class TeamResponse(BaseModel):
    id: int
    name: str
    owner_id: int
    role: str
    member_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


@router.get("/", response_model=List[TeamResponse])
async def list_teams(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(TeamMember, Team)
        .join(Team, Team.id == TeamMember.team_id)
        .filter(TeamMember.user_id == current_user.id)
    )
    rows = result.all()
    out = []
    for member, team in rows:
        count_res = await db.execute(
            select(TeamMember).filter(TeamMember.team_id == team.id)
        )
        out.append(
            TeamResponse(
                id=team.id,
                name=team.name,
                owner_id=team.owner_id,
                role=member.role,
                member_count=len(count_res.scalars().all()),
                created_at=team.created_at,
            )
        )
    return out


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team = Team(name=data.name, owner_id=current_user.id)
    db.add(team)
    await db.flush()
    db.add(TeamMember(team_id=team.id, user_id=current_user.id, role="owner"))
    await db.commit()
    await db.refresh(team)
    return TeamResponse(
        id=team.id,
        name=team.name,
        owner_id=team.owner_id,
        role="owner",
        member_count=1,
        created_at=team.created_at,
    )


@router.post("/{team_id}/invite")
async def invite_member(
    team_id: int,
    invite: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    member_res = await db.execute(
        select(TeamMember).filter(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.role.in_(["owner", "admin"]),
        )
    )
    if not member_res.scalars().first():
        raise HTTPException(status_code=403, detail="Not allowed to invite")

    team_res = await db.execute(select(Team).filter(Team.id == team_id))
    team = team_res.scalars().first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    user_res = await db.execute(select(User).filter(User.email == invite.email))
    user = user_res.scalars().first()
    if user:
        existing = await db.execute(
            select(TeamMember).filter(
                TeamMember.team_id == team_id, TeamMember.user_id == user.id
            )
        )
        if existing.scalars().first():
            raise HTTPException(status_code=400, detail="User already in team")
        db.add(TeamMember(team_id=team_id, user_id=user.id, role=invite.role))
        await db.commit()
    else:
        EmailService().send_team_invite(invite.email, team.name, current_user.full_name or current_user.email)

    return {"message": f"Invitation sent to {invite.email}"}


@router.get("/{team_id}/members")
async def list_members(
    team_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check = await db.execute(
        select(TeamMember).filter(
            TeamMember.team_id == team_id, TeamMember.user_id == current_user.id
        )
    )
    if not check.scalars().first():
        raise HTTPException(status_code=403, detail="Not a team member")

    result = await db.execute(
        select(TeamMember, User)
        .join(User, User.id == TeamMember.user_id)
        .filter(TeamMember.team_id == team_id)
    )
    return [
        {
            "user_id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": m.role,
            "avatar_url": u.avatar_url,
        }
        for m, u in result.all()
    ]
