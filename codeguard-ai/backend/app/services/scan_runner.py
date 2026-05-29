import asyncio
import os
import re
import shutil
import stat
import tempfile
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import OperationalError
from sqlalchemy.future import select

from app.models.scan_result import ScanResult
from app.models.project import Project
from app.core.config import settings
from app.schemas.analysis import Finding
from app.services.analyzer_service import AnalyzerService
from app.services.scan_events import publish_scan_event
from app.services.email_service import EmailService


class ScanRunner:
    """Runs the scan pipeline and persists results.

    This implementation intentionally works without Celery/Redis.
    """

    def __init__(self, analyzer: Optional[AnalyzerService] = None):
        self.analyzer = analyzer or AnalyzerService()
        self._copy_excluded_dirs = {
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            ".cache",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            ".scan_workdir",
            ".next",
            ".vercel",
            "node_modules",
            "venv",
            ".venv",
            "dist",
            "build",
        }
        self._copy_excluded_file_suffixes = {
            ".db",
            ".db-shm",
            ".db-wal",
            ".log",
            ".pyc",
            ".pyo",
            ".tmp",
        }

    async def run_scan(self, scan_id: int, db: AsyncSession) -> None:
        scan = await self._get_scan(scan_id, db)
        if not scan:
            return

        # Mark running
        scan.status = "running"
        scan.progress = 10
        scan.message = "Scan started"
        scan.error_message = None
        scan.risk_score = 0
        scan.findings = []
        await self._commit_with_retry(db)
        await db.refresh(scan)
        publish_scan_event(scan_id, {"status": "running", "progress": 10, "message": "Scan started"})

        try:
            project = await self._get_project(scan.project_id, db)
            if not project:
                raise RuntimeError("Project not found for scan")

            publish_scan_event(scan_id, {"status": "running", "progress": 25, "message": "Preparing workspace"})
            await self._update_progress(scan, db, 25, "Preparing workspace")
            workdir = await self._prepare_workspace(
                project.repository_url,
                github_token=getattr(project.owner, "github_access_token", None) if hasattr(project, "owner") else None,
            )

            publish_scan_event(scan_id, {"status": "running", "progress": 50, "message": "Running security analysis"})
            await self._update_progress(scan, db, 50, "Running security analysis")
            findings: List[Finding] = []
            findings = await asyncio.to_thread(self.analyzer.run_full_analysis, workdir)
            risk_score = await asyncio.to_thread(self.analyzer.calculate_risk_score, findings)

            publish_scan_event(scan_id, {"status": "running", "progress": 80, "message": "Running quality gates"})
            await self._update_progress(scan, db, 80, "Running quality gates")
            quality_gate_result = await asyncio.to_thread(
                self.analyzer.run_quality_gates, findings, risk_score
            )

            publish_scan_event(scan_id, {"status": "running", "progress": 90, "message": "Saving results"})
            await self._update_progress(scan, db, 90, "Saving results")
            scan.findings = [f.model_dump() for f in findings]
            scan.risk_score = risk_score
            scan.quality_gate_result = quality_gate_result
            scan.status = "completed"
            scan.progress = 100
            scan.message = "Scan complete"
            scan.error_message = None
            scan.completed_at = datetime.now(timezone.utc)
            await self._commit_with_retry(db)

            publish_scan_event(
                scan_id,
                {
                    "status": "completed",
                    "progress": 100,
                    "message": "Scan complete",
                    "risk_score": risk_score,
                    "findings_count": len(findings),
                },
            )
            await self._notify_scan_complete(scan_id, db, project, risk_score, len(findings))
        except Exception as e:
            await db.rollback()
            scan = await self._get_scan(scan_id, db)
            if scan:
                scan.status = "failed"
                scan.progress = 100
                scan.message = "Scan failed"
                scan.error_message = str(e)
                scan.completed_at = datetime.now(timezone.utc)
                await self._commit_with_retry(db)
            publish_scan_event(scan_id, {"status": "failed", "progress": 100, "message": str(e)})
            print(f"Scan failed: {str(e)}")
            traceback.print_exc()
        finally:
            await self._cleanup_workspace()

    async def _get_scan(self, scan_id: int, db: AsyncSession) -> Optional[ScanResult]:
        res = await db.execute(select(ScanResult).filter(ScanResult.id == scan_id))
        return res.scalars().first()

    async def _get_project(self, project_id: int, db: AsyncSession) -> Optional[Project]:
        from app.models.user import User

        res = await db.execute(select(Project).filter(Project.id == project_id))
        project = res.scalars().first()
        if project:
            owner_res = await db.execute(select(User).filter(User.id == project.owner_id))
            project.owner = owner_res.scalars().first()  # type: ignore[attr-defined]
        return project

    async def _update_progress(self, scan: ScanResult, db: AsyncSession, progress: int, message: str) -> None:
        scan.progress = progress
        scan.message = message
        await self._commit_with_retry(db)

    async def _commit_with_retry(self, db: AsyncSession, attempts: int = 5) -> None:
        for attempt in range(attempts):
            try:
                await db.commit()
                return
            except OperationalError as exc:
                await db.rollback()
                if "database is locked" not in str(exc).lower() or attempt == attempts - 1:
                    raise
                await asyncio.sleep(0.25 * (attempt + 1))

    async def _notify_scan_complete(
        self, scan_id: int, db: AsyncSession, project: Project, risk_score: int, findings_count: int
    ) -> None:
        from app.models.user import User

        owner_res = await db.execute(select(User).filter(User.id == project.owner_id))
        owner = owner_res.scalars().first()
        if not owner or not owner.email:
            return
        EmailService().send_scan_complete(
            owner.email,
            project.name,
            scan_id,
            "completed",
            risk_score,
            findings_count,
        )

    def _is_git_url(self, url: str) -> bool:
        return bool(
            re.match(r"^https?://", url, re.I)
            or re.match(r"^git@", url, re.I)
            or url.endswith(".git")
        )

    async def _clone_repository(self, url: str, workdir: str) -> None:
        """Shallow-clone a remote repository into workdir."""
        proc = await asyncio.create_subprocess_exec(
            "git",
            "clone",
            "--depth",
            "1",
            url,
            workdir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            raise RuntimeError("Git clone timed out after 30 seconds")
        if proc.returncode != 0:
            raise RuntimeError(
                f"Git clone failed: {stderr.decode(errors='replace').strip() or 'unknown error'}"
            )

    async def _prepare_workspace(self, repository_url: Optional[str], github_token: Optional[str] = None) -> str:
        """Create a local directory and populate it from a repo URL or local path.

        If no URL is given and ENABLE_DEMO_FINDINGS is True the scanners will
        generate synthetic findings on the empty workdir — no crash occurs.
        If ENABLE_DEMO_FINDINGS is False an empty workdir is returned and the
        scan will legitimately report zero findings (nothing to scan).
        """
        base = self._workspace_base()
        os.makedirs(base, exist_ok=True)
        workdir = os.path.join(base, f"work_{uuid.uuid4().hex}")
        os.makedirs(workdir, exist_ok=True)

        if not repository_url:
            # No source specified — scanners with ENABLE_DEMO_FINDINGS will
            # inject synthetic findings; others will just return empty.
            return workdir

        if os.path.exists(repository_url):
            await asyncio.to_thread(self._copy_source_tree, repository_url, workdir)
            return workdir

        if self._is_git_url(repository_url):
            clone_url = repository_url
            if github_token and "github.com" in repository_url:
                clone_url = repository_url.replace(
                    "https://", f"https://{github_token}@"
                )
            clone_target = workdir + "_clone"
            try:
                try:
                    await self._clone_repository(clone_url, clone_target)
                except RuntimeError:
                    if settings.ENABLE_DEMO_FINDINGS:
                        # Clone failed but demo mode is on — still run scanners.
                        return workdir
                    raise
                items = os.listdir(clone_target)
                for item in items:
                    s = os.path.join(clone_target, item)
                    d = os.path.join(workdir, item)
                    if os.path.isdir(s):
                        self._copy_source_tree(s, d)
                    else:
                        self._copy_file_best_effort(s, d)
            finally:
                if os.path.exists(clone_target):
                    shutil.rmtree(clone_target, ignore_errors=True, onerror=self._remove_readonly)

        return workdir

    def _workspace_base(self) -> str:
        return os.path.join(tempfile.gettempdir(), "codeguard_scan_workdir")

    def _copy_source_tree(self, source: str, destination: str) -> None:
        """Copy scan-worthy source files while avoiding Windows-locked folders."""
        try:
            os.makedirs(destination, exist_ok=True)
        except OSError as exc:
            print(f"Skipping unreadable scan destination {destination}: {exc}")
            return

        try:
            for root, dirs, files in os.walk(source, topdown=True, onerror=self._handle_walk_error):
                dirs[:] = [name for name in dirs if not self._should_skip_name(name)]

                for name in list(dirs):
                    path = os.path.join(root, name)
                    if not os.path.exists(path) or not os.access(path, os.R_OK | os.X_OK):
                        dirs.remove(name)

                rel_root = os.path.relpath(root, source)
                target_root = destination if rel_root == "." else os.path.join(destination, rel_root)
                os.makedirs(target_root, exist_ok=True)

                for file_name in files:
                    if self._should_skip_name(file_name):
                        continue

                    src = os.path.join(root, file_name)
                    dst = os.path.join(target_root, file_name)
                    try:
                        if not os.path.exists(src) or not os.access(src, os.R_OK):
                            continue
                        self._copy_file_best_effort(src, dst)
                    except OSError as exc:
                        print(f"Skipping unreadable scan path {src}: {exc}")
        except OSError as exc:
            print(f"Skipping unreadable scan directory {source}: {exc}")

    def _should_skip_name(self, name: str) -> bool:
        lower_name = name.lower()
        return (
            name in self._copy_excluded_dirs
            or any(lower_name.endswith(suffix) for suffix in self._copy_excluded_file_suffixes)
        )

    def _ignore_scan_copy_paths(self, directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            path = os.path.join(directory, name)
            if self._should_skip_name(name):
                ignored.add(name)
                continue
            try:
                mode = os.stat(path).st_mode
            except OSError:
                ignored.add(name)
                continue
            if not mode & stat.S_IRUSR:
                ignored.add(name)
        return ignored

    def _copy_file_best_effort(self, source: str, destination: str) -> str:
        if self._should_skip_name(os.path.basename(source)):
            return destination

        try:
            if not os.path.exists(source) or not os.access(source, os.R_OK):
                return destination

            os.makedirs(os.path.dirname(destination), exist_ok=True)
            shutil.copy2(source, destination, follow_symlinks=False)
            return destination
        except (PermissionError, OSError) as exc:
            print(f"Skipping unreadable scan file {source}: {exc}")
            return destination

    def _handle_walk_error(self, exc: OSError) -> None:
        print(f"Skipping unreadable scan path during walk: {exc}")

    async def _cleanup_workspace(self) -> None:
        # Remove scan_workdir entirely if exists (best-effort).
        base = self._workspace_base()
        if os.path.exists(base):
            try:
                await asyncio.to_thread(
                    shutil.rmtree,
                    base,
                    ignore_errors=True,
                    onerror=self._remove_readonly,
                )
            except Exception:
                pass

    def _remove_readonly(self, func, path: str, exc_info) -> None:
        try:
            os.chmod(path, stat.S_IWRITE)
            func(path)
        except Exception as exc:
            print(f"Skipping locked cleanup path {path}: {exc}")
