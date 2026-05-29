"""
Duplicate Code Analyzer — detects copy-paste/cloned code blocks using line-fingerprint hashing.
Works across Python, JavaScript, TypeScript, Java, and other text-based source files.
"""
import os
import re
import hashlib
from collections import defaultdict
from typing import List
from app.schemas.analysis import Finding


class DuplicateCodeAnalyzer:
    SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".cs"}
    # Minimum number of consecutive non-trivial lines to flag as a duplicate
    MIN_BLOCK_LINES = 6

    def scan(self, directory_path: str) -> List[Finding]:
        # Map: fingerprint -> list of (file_path, start_line)
        block_map: dict[str, list[tuple[str, int]]] = defaultdict(list)
        file_lines: dict[str, list[str]] = {}

        for root, dirs, files in os.walk(directory_path):
            dirs[:] = [d for d in dirs if d not in {"node_modules", ".git", "__pycache__", "venv", ".venv", "dist", "build"}]
            for fname in files:
                ext = os.path.splitext(fname)[1].lower()
                if ext not in self.SUPPORTED_EXTENSIONS:
                    continue
                fpath = os.path.join(root, fname)
                rel_path = os.path.relpath(fpath, directory_path)
                try:
                    with open(fpath, encoding="utf-8", errors="ignore") as f:
                        raw_lines = f.readlines()
                    file_lines[rel_path] = raw_lines
                    # Normalize: strip whitespace and skip blank/comment-only lines
                    normalized = [self._normalize(l) for l in raw_lines]
                    self._index_blocks(rel_path, normalized, block_map)
                except Exception:
                    continue

        return self._build_findings(block_map, file_lines)

    def _normalize(self, line: str) -> str:
        """Strip whitespace and inline comments for comparison."""
        line = line.strip()
        # Remove Python/JS single-line comments
        line = re.sub(r"#.*$", "", line)
        line = re.sub(r"//.*$", "", line)
        return line.strip()

    def _index_blocks(self, rel_path: str, normalized: list[str], block_map: dict) -> None:
        """Slide a window of MIN_BLOCK_LINES non-trivial lines across the file."""
        non_trivial = [(i, l) for i, l in enumerate(normalized) if len(l) > 3]
        n = len(non_trivial)
        window = self.MIN_BLOCK_LINES
        for i in range(n - window + 1):
            chunk = "\n".join(l for _, l in non_trivial[i:i + window])
            fp = hashlib.md5(chunk.encode()).hexdigest()
            start_line = non_trivial[i][0] + 1  # 1-indexed
            block_map[fp].append((rel_path, start_line))

    def _build_findings(self, block_map: dict, file_lines: dict) -> List[Finding]:
        findings = []
        reported: set[tuple[str, int]] = set()

        for fp, locations in block_map.items():
            if len(locations) < 2:
                continue
            # Deduplicate — same file, adjacent starts are part of same clone
            seen_files: dict[str, int] = {}
            filtered = []
            for fpath, lineno in locations:
                prev = seen_files.get(fpath)
                if prev is None or abs(lineno - prev) > self.MIN_BLOCK_LINES:
                    filtered.append((fpath, lineno))
                    seen_files[fpath] = lineno

            if len(filtered) < 2:
                continue

            # Report each occurrence
            locations_str = "; ".join(f"{f}:{l}" for f, l in filtered[:3])
            if len(filtered) > 3:
                locations_str += f" (+{len(filtered) - 3} more)"

            for fpath, lineno in filtered:
                key = (fpath, lineno)
                if key in reported:
                    continue
                reported.add(key)

                snippet_lines = file_lines.get(fpath, [])
                snippet = "".join(snippet_lines[lineno - 1 : lineno + 3]).strip()

                findings.append(Finding(
                    tool="duplicate-code-analyzer",
                    rule_id="DUP001",
                    message=f"Duplicate code block detected. Same logic exists at: {locations_str}",
                    file_path=fpath,
                    line_number=lineno,
                    severity="warning",
                    code_snippet=snippet[:300] if snippet else None,
                ))

        return findings
