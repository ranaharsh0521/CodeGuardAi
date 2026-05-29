from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Suppress passlib's bcrypt version detection warning (bcrypt >= 4.x)
import warnings
warnings.filterwarnings("ignore", ".*error reading bcrypt version.*")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

# bcrypt silently truncates at 72 bytes — we enforce this to avoid ValueError.
_BCRYPT_MAX = 72

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Truncate to 72 bytes before verifying to match hashing behavior
    truncated = plain_password.encode("utf-8")[:_BCRYPT_MAX].decode("utf-8", errors="ignore")
    return pwd_context.verify(truncated, hashed_password)

def get_password_hash(password: str) -> str:
    # bcrypt only hashes the first 72 bytes — truncate explicitly
    truncated = password.encode("utf-8")[:_BCRYPT_MAX].decode("utf-8", errors="ignore")
    return pwd_context.hash(truncated)
