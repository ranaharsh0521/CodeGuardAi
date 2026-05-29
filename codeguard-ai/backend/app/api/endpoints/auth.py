from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import timedelta
from urllib.parse import urlencode
import httpx
import secrets

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, Token, UserResponse

router = APIRouter()


def _is_local_url(url: str) -> bool:
    return "localhost" in url or "127.0.0.1" in url


def _dev_oauth_fallback_enabled() -> bool:
    return (
        settings.DEV_OAUTH_FALLBACK
        and _is_local_url(settings.BACKEND_URL)
        and _is_local_url(settings.FRONTEND_URL)
    )


def _oauth_error_redirect(provider: str, message: str) -> RedirectResponse:
    params = urlencode({"provider": provider, "error": message})
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/oauth/callback?{params}")


async def _login_dev_oauth_user(provider: str, db: AsyncSession) -> RedirectResponse:
    if provider not in {"github", "google"}:
        raise HTTPException(status_code=404, detail="Unknown OAuth provider")

    provider_name = "GitHub" if provider == "github" else "Google"
    provider_id = f"dev-{provider}"
    email = f"dev-{provider}@example.com"
    legacy_email = f"dev-{provider}@codeguard.local"

    if provider == "github":
        result = await db.execute(select(User).filter(User.github_id == provider_id))
    else:
        result = await db.execute(select(User).filter(User.google_id == provider_id))
    user = result.scalars().first()

    if not user:
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()

    if not user:
        result = await db.execute(select(User).filter(User.email == legacy_email))
        user = result.scalars().first()

    if user:
        user.email = email
        user.full_name = user.full_name or f"Dev {provider_name} User"
        if provider == "github":
            user.github_id = provider_id
            user.github_username = user.github_username or provider_id
        else:
            user.google_id = provider_id
        user.avatar_url = user.avatar_url or f"https://api.dicebear.com/9.x/initials/svg?seed={provider_name}"
    else:
        user = User(
            email=email,
            full_name=f"Dev {provider_name} User",
            hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            github_id=provider_id if provider == "github" else None,
            github_username=provider_id if provider == "github" else None,
            google_id=provider_id if provider == "google" else None,
            avatar_url=f"https://api.dicebear.com/9.x/initials/svg?seed={provider_name}",
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    jwt = create_access_token(subject=user.id, expires_delta=timedelta(days=8))
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/oauth/callback?token={jwt}&provider={provider}")


@router.get("/dev/{provider}")
async def dev_oauth_login(provider: str, db: AsyncSession = Depends(get_db)):
    """Local-only OAuth fallback used when real Google/GitHub credentials are missing."""
    if not _dev_oauth_fallback_enabled():
        raise HTTPException(status_code=503, detail="Development OAuth fallback is disabled")
    return await _login_dev_oauth_user(provider, db)

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_data.email))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    
    return db_user

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login user and return access token"""
    result = await db.execute(select(User).filter(User.email == credentials.email))
    user = result.scalars().first()
    
    if not user or not user.hashed_password or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    access_token_expires = timedelta(days=8)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
async def logout():
    """Logout user (client should discard token)"""
    return {"message": "Successfully logged out"}


@router.get("/github/login")
async def github_login():
    """Return GitHub OAuth authorization URL."""
    if not settings.GITHUB_CLIENT_ID:
        if _dev_oauth_fallback_enabled():
            return {"authorization_url": f"{settings.BACKEND_URL}{settings.API_V1_STR}/auth/dev/github"}
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="GitHub OAuth not configured. Set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET in .env",
        )
    params = urlencode(
        {
            "client_id": settings.GITHUB_CLIENT_ID,
            "redirect_uri": settings.GITHUB_REDIRECT_URI,
            "scope": "read:user user:email repo",
        }
    )
    return {"authorization_url": f"https://github.com/login/oauth/authorize?{params}"}


@router.get("/github/callback")
async def github_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Exchange GitHub code for token, create/login user, redirect to frontend."""
    if not settings.GITHUB_CLIENT_ID or not settings.GITHUB_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="GitHub OAuth not configured")

    try:
        async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
            token_res = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": settings.GITHUB_REDIRECT_URI,
                },
            )
            token_data = token_res.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return _oauth_error_redirect(
                    "github",
                    token_data.get("error_description", "GitHub sign-in failed. Please try again."),
                )

            user_res = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_res.raise_for_status()
            gh_user = user_res.json()

            email = gh_user.get("email")
            if not email:
                emails_res = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                emails_res.raise_for_status()
                emails = emails_res.json()
                primary = next((e for e in emails if e.get("primary")), None)
                email = primary["email"] if primary else f"{gh_user['id']}@users.noreply.github.com"
    except (httpx.HTTPError, ValueError):
        if _dev_oauth_fallback_enabled():
            return await _login_dev_oauth_user("github", db)
        return _oauth_error_redirect(
            "github",
            "GitHub sign-in could not contact GitHub. Check internet or proxy settings and try again.",
        )

    github_id = str(gh_user["id"])
    result = await db.execute(select(User).filter(User.github_id == github_id))
    user = result.scalars().first()

    if not user:
        email_result = await db.execute(select(User).filter(User.email == email))
        user = email_result.scalars().first()

    if user:
        user.github_id = github_id
        user.github_username = gh_user.get("login")
        user.github_access_token = access_token
        user.avatar_url = gh_user.get("avatar_url")
        if not user.full_name:
            user.full_name = gh_user.get("name") or gh_user.get("login")
    else:
        user = User(
            email=email,
            full_name=gh_user.get("name") or gh_user.get("login"),
            hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            github_id=github_id,
            github_username=gh_user.get("login"),
            github_access_token=access_token,
            avatar_url=gh_user.get("avatar_url"),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    jwt = create_access_token(subject=user.id, expires_delta=timedelta(days=8))
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/oauth/callback?token={jwt}&provider=github")


@router.get("/google/login")
async def google_login():
    """Return Google OAuth authorization URL."""
    if not settings.GOOGLE_CLIENT_ID:
        if _dev_oauth_fallback_enabled():
            return {"authorization_url": f"{settings.BACKEND_URL}{settings.API_V1_STR}/auth/dev/google"}
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env",
        )
    params = urlencode(
        {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "select_account",
        }
    )
    return {"authorization_url": f"https://accounts.google.com/o/oauth2/v2/auth?{params}"}


@router.get("/google/callback")
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Exchange Google code for token, create/login user, redirect to frontend."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(status_code=503, detail="Google OAuth not configured")

    try:
        async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
            token_res = await client.post(
                "https://oauth2.googleapis.com/token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
            )
            token_data = token_res.json()
            access_token = token_data.get("access_token")
            if not access_token:
                return _oauth_error_redirect(
                    "google",
                    token_data.get("error_description", "Google sign-in failed. Please try again."),
                )

            user_res = await client.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_res.raise_for_status()
            google_user = user_res.json()
    except (httpx.HTTPError, ValueError):
        if _dev_oauth_fallback_enabled():
            return await _login_dev_oauth_user("google", db)
        return _oauth_error_redirect(
            "google",
            "Google sign-in could not contact Google. Check internet or proxy settings and try again.",
        )

    google_id = google_user.get("sub")
    email = google_user.get("email")
    if not google_id or not email:
        raise HTTPException(status_code=400, detail="Google account did not return an email")

    result = await db.execute(select(User).filter(User.google_id == google_id))
    user = result.scalars().first()

    if not user:
        email_result = await db.execute(select(User).filter(User.email == email))
        user = email_result.scalars().first()

    if user:
        user.google_id = google_id
        user.avatar_url = google_user.get("picture") or user.avatar_url
        if not user.full_name:
            user.full_name = google_user.get("name") or email
    else:
        user = User(
            email=email,
            full_name=google_user.get("name") or email,
            hashed_password=get_password_hash(secrets.token_urlsafe(32)),
            google_id=google_id,
            avatar_url=google_user.get("picture"),
        )
        db.add(user)

    await db.commit()
    await db.refresh(user)

    jwt = create_access_token(subject=user.id, expires_delta=timedelta(days=8))
    return RedirectResponse(f"{settings.FRONTEND_URL}/auth/oauth/callback?token={jwt}&provider=google")
