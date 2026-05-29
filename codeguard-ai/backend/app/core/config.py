from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "CodeGuard AI"
    API_V1_STR: str = "/api/v1"

    # CORS & Frontend
    # Stored as a comma-separated string in .env so pydantic-settings parses it correctly.
    # Use the `cors_origins` property wherever a list is needed (e.g. CORSMiddleware).
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"

    @property
    def cors_origins(self) -> List[str]:
        """Return BACKEND_CORS_ORIGINS as a clean list of URLs."""
        return [
            o.strip().rstrip("/")
            for o in self.BACKEND_CORS_ORIGINS.split(",")
            if o.strip()
        ]
    
    # Database - Using SQLite for development
    DATABASE_URL: str = "sqlite+aiosqlite:///./codeguard.db"
    
    # Legacy PostgreSQL settings (kept for production)
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "codeguard"
    POSTGRES_PORT: str = "5432"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        # Use SQLite by default, PostgreSQL if DATABASE_URL is explicitly set to postgres
        if hasattr(self, '_database_url_override'):
            return self._database_url_override
        return self.DATABASE_URL
    
    # Security
    SECRET_KEY: str = "supersecretkey_please_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    # AI API
    AI_PROVIDER: str = "openai"  # openai, claude, or grok
    AI_API_KEY: Optional[str] = None

    # Development/demo behavior
    ENABLE_DEMO_FINDINGS: bool = False
    DEV_OAUTH_FALLBACK: bool = False
    SCAN_TIMEOUT_SECONDS: int = 180
    
    # GitHub OAuth
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None

    @field_validator('GITHUB_CLIENT_ID', 'GITHUB_CLIENT_SECRET', 'GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET', mode='before')
    @classmethod
    def empty_or_placeholder_to_none(cls, v: Optional[str]) -> Optional[str]:
        if not v or v.startswith('REPLACE_WITH'):
            return None
        return v

    @property
    def GITHUB_REDIRECT_URI(self) -> str:
        return f"{self.BACKEND_URL}{self.API_V1_STR}/auth/github/callback"

    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return f"{self.BACKEND_URL}{self.API_V1_STR}/auth/google/callback"
    
    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    USE_CELERY: bool = False

    # Email (optional — scans won't email if unset)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
