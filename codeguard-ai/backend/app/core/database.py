from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import event, inspect, text
from app.core.config import settings

is_sqlite = settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite")

engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    echo=False,
    future=True,
    connect_args={"timeout": 30} if is_sqlite else {},
)

if is_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

# Import all models so they register with Base
from app.models.user import User  # noqa: E402, F401
from app.models.project import Project  # noqa: E402, F401
from app.models.scan_result import ScanResult  # noqa: E402, F401
from app.models.team import Team, TeamMember  # noqa: E402, F401
from app.models.scheduled_scan import ScheduledScan  # noqa: E402, F401


async def run_migrations(conn) -> None:
    """Add new columns to existing SQLite DBs (dev-friendly)."""

    def _migrate(sync_conn):
        insp = inspect(sync_conn)

        def add_column(table: str, column: str, col_type: str) -> None:
            if table not in insp.get_table_names():
                return
            existing = [c["name"] for c in insp.get_columns(table)]
            if column not in existing:
                sync_conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"))

        add_column("users", "github_username", "VARCHAR")
        add_column("users", "github_access_token", "VARCHAR")
        add_column("users", "avatar_url", "VARCHAR")
        add_column("users", "google_id", "VARCHAR")
        add_column("projects", "team_id", "INTEGER")
        add_column("scan_results", "progress", "INTEGER DEFAULT 0")
        add_column("scan_results", "message", "VARCHAR")
        add_column("scan_results", "error_message", "VARCHAR")
        add_column("scan_results", "quality_gate_result", "JSON")

        if "scan_results" in insp.get_table_names():
            sync_conn.execute(
                text(
                    """
                    UPDATE scan_results
                    SET status = 'failed',
                        progress = 100,
                        message = 'Scan interrupted',
                        error_message = 'Scan was interrupted before completion. Start a new scan.',
                        completed_at = CURRENT_TIMESTAMP
                    WHERE status IN ('pending', 'running')
                    AND datetime(created_at) < datetime('now', '-10 minutes')
                    """
                )
            )

        if "users" in insp.get_table_names():
            sync_conn.execute(
                text(
                    """
                    UPDATE users
                    SET email = 'dev-github@example.com'
                    WHERE email = 'dev-github@codeguard.local'
                    AND NOT EXISTS (
                        SELECT 1 FROM users WHERE email = 'dev-github@example.com'
                    )
                    """
                )
            )
            sync_conn.execute(
                text(
                    """
                    UPDATE users
                    SET email = 'dev-google@example.com'
                    WHERE email = 'dev-google@codeguard.local'
                    AND NOT EXISTS (
                        SELECT 1 FROM users WHERE email = 'dev-google@example.com'
                    )
                    """
                )
            )

    await conn.run_sync(_migrate)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
