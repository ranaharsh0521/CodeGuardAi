from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    token = credentials.credentials

    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        raw_sub = payload.get("sub")

        if raw_sub is None:
            raise credentials_error

        # sub is always stored as a string (str(user.id)) — cast to int explicitly
        try:
            user_id = int(raw_sub)
        except (TypeError, ValueError):
            raise credentials_error

    except JWTError:
        raise credentials_error

    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    is_dev_oauth_user = (
        user.email in {"dev-google@example.com", "dev-github@example.com"}
        or user.google_id == "dev-google"
        or user.github_id == "dev-github"
    )
    if is_dev_oauth_user and not settings.DEV_OAUTH_FALLBACK:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Development OAuth users are disabled"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is inactive"
        )

    return user
