import os
import re
from typing import List

from app.schemas.analysis import Finding


class DependencyScanner:
    """Lightweight dependency hygiene checks (no external audit tools required)."""

    def scan(self, directory_path: str) -> List[Finding]:
        findings: List[Finding] = []
        findings.extend(self._check_python_deps(directory_path))
        findings.extend(self._check_node_deps(directory_path))
        return findings

    def _check_python_deps(self, root: str) -> List[Finding]:
        findings = []
        for dirpath, _, filenames in os.walk(root):
            if "requirements.txt" in filenames:
                path = os.path.join(dirpath, "requirements.txt")
                with open(path, encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                unpinned = [
                    ln.strip()
                    for ln in lines
                    if ln.strip()
                    and not ln.strip().startswith("#")
                    and "==" not in ln
                    and ">=" not in ln
                    and "<=" not in ln
                ]
                if unpinned:
                    findings.append(
                        Finding(
                            tool="dependency-scanner",
                            rule_id="unpinned-python-deps",
                            message=f"Unpinned Python dependencies in requirements.txt ({len(unpinned)} packages)",
                            file_path=os.path.relpath(path, root),
                            line_number=1,
                            severity="warning",
                            code_snippet="\n".join(unpinned[:5]),
                        )
                    )
            if "Pipfile" in filenames and "Pipfile.lock" not in filenames:
                findings.append(
                    Finding(
                        tool="dependency-scanner",
                        rule_id="missing-pipfile-lock",
                        message="Pipfile found without Pipfile.lock — builds may not be reproducible",
                        file_path=os.path.relpath(os.path.join(dirpath, "Pipfile"), root),
                        line_number=1,
                        severity="warning",
                    )
                )
        return findings

    def _check_node_deps(self, root: str) -> List[Finding]:
        findings = []
        for dirpath, _, filenames in os.walk(root):
            if "package.json" not in filenames:
                continue
            pkg_path = os.path.join(dirpath, "package.json")
            has_lock = "package-lock.json" in filenames or "yarn.lock" in filenames or "pnpm-lock.yaml" in filenames
            if not has_lock:
                findings.append(
                    Finding(
                        tool="dependency-scanner",
                        rule_id="missing-lockfile",
                        message="package.json without lock file — dependency versions are not pinned",
                        file_path=os.path.relpath(pkg_path, root),
                        line_number=1,
                        severity="warning",
                    )
                )
            with open(pkg_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if re.search(r'"\^|"\~|"\*', content):
                findings.append(
                    Finding(
                        tool="dependency-scanner",
                        rule_id="loose-semver-ranges",
                        message="Loose semver ranges (^, ~, *) in package.json increase supply-chain risk",
                        file_path=os.path.relpath(pkg_path, root),
                        line_number=1,
                        severity="info",
                    )
                )
        return findings
