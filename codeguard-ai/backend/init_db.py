#!/usr/bin/env python3
"""
Database initialization script.
Run this to create all database tables (non-destructive — existing data is kept).
"""
import asyncio
from app.core.database import engine, Base

# Import every model so it registers with Base.metadata before create_all.
from app.models.user import User  # noqa: F401
from app.models.project import Project  # noqa: F401
from app.models.scan_result import ScanResult  # noqa: F401
from app.models.team import Team, TeamMember  # noqa: F401
from app.models.scheduled_scan import ScheduledScan  # noqa: F401


async def init_db():
    """Create all database tables.  Existing tables are left untouched."""
    print("Initialising database…")
    async with engine.begin() as conn:
        # create_all is idempotent — it skips tables that already exist.
        await conn.run_sync(Base.metadata.create_all)
    print("Database ready.")


if __name__ == "__main__":
    asyncio.run(init_db())