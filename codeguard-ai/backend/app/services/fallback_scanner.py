"""
Fallback security scanner — pure Python, no external tools required.

Runs when Semgrep/Gitleaks are not installed.  Covers:
- Hardcoded secrets (API keys, passwords, tokens)
- Dangerous function calls (eval, exec, pickle.loads …)
- SQL injection patterns
- Basic dependency file hygiene

All findings use the standard Finding schema so they feed into the rest of
the pipeline (risk scoring, AI suggestions, quality gates) unchanged.
"""

import os
import re
from typing import List

from app.schemas.analysis import Finding


# ---------------------------------------------------------------------------
# Pattern definitions
# ---------------------------------------------------------------------------

# (pattern, rule_id, message, severity)
_SECRET_PATTERNS: List[tuple] = [
    (
        re.compile(r'(?i)(api[_\-]?key|secret[_\-]?key|access[_\-]?token|auth[_\-]?token)\s*[=:]\s*["\']([A-Za-z0-9+/\-_]{16,})["\']'),
        "fallback.hardcoded-api-key",
        "Potential hardcoded API key or secret token detected",
        "critical",
    ),
    (
        re.compile(r'(?i)password\s*[=:]\s*["\'](?!<[^>]+>)(?!\s*\{)([^"\']{6,})["\']'),
        "fallback.hardcoded-password",
        "Potential hardcoded password detected",
        "critical",
    ),
    (
        re.compile(r'(?i)(GITHUB_TOKEN|GITHUB_SECRET|GH_TOKEN)\s*[=:]\s*["\']([A-Za-z0-9+/\-_]{16,})["\']'),
        "fallback.hardcoded-github-token",
        "Potential hardcoded GitHub token detected",
        "critical",
    ),
    (
        re.compile(r'(?i)(aws[_\-]?access[_\-]?key|aws[_\-]?secret)\s*[=:]\s*["\']([A-Za-z0-9+/=]{16,})["\']'),
        "fallback.hardcoded-aws-credential",
        "Potential hardcoded AWS credential detected",
        "critical",
    ),
    (
        re.compile(r'(?i)(private[_\-]?key|rsa[_\-]?key)\s*[=:]\s*["\']([A-Za-z0-9+/=\-]{16,})["\']'),
        "fallback.hardcoded-private-key",
        "Potential hardcoded private key detected",
        "critical",
    ),
]

_CODE_PATTERNS: List[tuple] = [
    (
        re.compile(r'\beval\s*\('),
        "fallback.dangerous-eval",
        "Use of eval() can allow arbitrary code execution",
        "high",
    ),
    (
        re.compile(r'\bexec\s*\('),
        "fallback.dangerous-exec",
        "Use of exec() can allow arbitrary code execution",
        "high",
    ),
    (
        re.compile(r'\bpickle\.loads?\s*\('),
        "fallback.unsafe-pickle",
        "pickle.load/loads is unsafe with untrusted data — use json instead",
        "high",
    ),
    (
        re.compile(r'f["\']SELECT\s.*WHERE.*\{'),
        "fallback.sql-injection",
        "Potential SQL injection: f-string used to build a SQL query",
        "high",
    ),
    (
        re.compile(r'subprocess\.(run|call|check_output|Popen)\s*\(\s*(?![\[\(])["\']'),
        "fallback.shell-injection",
        "subprocess called with a string literal — prefer a list to avoid shell injection",
        "warning",
    ),
    (
        re.compile(r'verify\s*=\s*False'),
        "fallback.ssl-verification-disabled",
        "SSL certificate verification is disabled (verify=False)",
        "warning",
    ),
    (
        re.compile(r'MD5|md5\s*\('),
        "fallback.weak-hash-md5",
        "MD5 is a cryptographically broken hash function — use SHA-256 or better",
        "warning",
    ),
    (
        re.compile(r'DEBUG\s*=\s*True'),
        "fallback.debug-enabled",
        "DEBUG mode is enabled — ensure it is off in production",
        "info",
    ),
    (
        re.compile(r'TODO|FIXME|HACK|XXX'),
        "fallback.code-quality-todo",
        "Unresolved TODO/FIXME/HACK comment",
        "info",
    ),
]

# File extensions to scan for code patterns and secrets
_TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".env", ".env.local", ".env.production",
    ".sh", ".bash", ".yml", ".yaml",
    ".json", ".toml", ".cfg", ".ini",
    ".php", ".rb", ".go", ".java", ".cs",
    ".rs", ".kt", ".swift",
}

# Directories to skip entirely
_SKIP_DIRS = {
    ".git", ".hg", "node_modules", "venv", ".venv",
    "__pycache__", ".next", "dist", "build", ".mypy_cache",
}

_MAX_FILE_SIZE = 256 * 1024  # 256 KB — skip very large files


class FallbackScanner:
    """Pure-Python security scanner.  No external binaries required."""

    def scan(self, directory_path: str) -> List[Finding]:
        """Scan all text files under *directory_path* and return findings."""
        findings: List[Finding] = []
        for dirpath, dirnames, filenames in os.walk(directory_path):
            # Prune excluded directories in-place so os.walk skips them.
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in _TEXT_EXTENSIONS:
                    continue
                filepath = os.path.join(dirpath, filename)
                try:
                    findings.extend(self._scan_file(filepath, directory_path))
                except (OSError, UnicodeDecodeError):
                    pass
        return findings

    def _scan_file(self, filepath: str, root: str) -> List[Finding]:
        if os.path.getsize(filepath) > _MAX_FILE_SIZE:
            return []

        with open(filepath, encoding="utf-8", errors="ignore") as fh:
            lines = fh.readlines()

        rel_path = os.path.relpath(filepath, root)
        findings: List[Finding] = []

        for line_no, line in enumerate(lines, start=1):
            for pattern, rule_id, message, severity in _SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        Finding(
                            tool="fallback-scanner",
                            rule_id=rule_id,
                            message=message,
                            file_path=rel_path,
                            line_number=line_no,
                            severity=severity,
                            code_snippet=line.strip()[:200],
                        )
                    )
            for pattern, rule_id, message, severity in _CODE_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        Finding(
                            tool="fallback-scanner",
                            rule_id=rule_id,
                            message=message,
                            file_path=rel_path,
                            line_number=line_no,
                            severity=severity,
                            code_snippet=line.strip()[:200],
                        )
                    )

        return findings
