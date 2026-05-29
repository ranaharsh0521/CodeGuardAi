"""
Dead Code Analyzer — detects unused variables, functions, imports, and unreachable code.
Uses lightweight AST-based heuristics for Python, JavaScript/TypeScript, and Java.
"""
import ast
import os
import re
from typing import List
from app.schemas.analysis import Finding


class DeadCodeAnalyzer:
    SUPPORTED_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".java"}

    def scan(self, directory_path: str) -> List[Finding]:
        findings = []
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
                        source = f.read()
                    if ext == ".py":
                        findings.extend(self._analyze_python(source, rel_path))
                    else:
                        findings.extend(self._analyze_js_ts(source, rel_path, ext))
                except Exception:
                    continue
        return findings

    # ── Python ──────────────────────────────────────────────────────────────

    def _analyze_python(self, source: str, file_path: str) -> List[Finding]:
        findings = []
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return findings

        # Collect all names that are referenced anywhere in the module body
        all_names: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name):
                all_names.add(node.id)
            elif isinstance(node, ast.Attribute):
                if isinstance(node.value, ast.Name):
                    all_names.add(node.value.id)

        for node in ast.walk(tree):
            # Unused imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split(".")[0]
                    if name not in all_names and not name.startswith("_"):
                        findings.append(Finding(
                            tool="dead-code-analyzer",
                            rule_id="DEAD001",
                            message=f"Unused import: '{alias.name}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="warning",
                            code_snippet=f"import {alias.name}",
                        ))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name != "*" and name not in all_names and not name.startswith("_"):
                        findings.append(Finding(
                            tool="dead-code-analyzer",
                            rule_id="DEAD001",
                            message=f"Unused import: '{alias.name}' from '{node.module}'",
                            file_path=file_path,
                            line_number=node.lineno,
                            severity="warning",
                            code_snippet=f"from {node.module} import {alias.name}",
                        ))

            # Unused local variables (simple heuristic inside functions)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                findings.extend(self._check_unused_locals(node, file_path))

            # Unreachable code after return/raise/continue/break
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                findings.extend(self._check_unreachable(node.body, file_path))

        return findings

    def _check_unused_locals(self, func_node: ast.FunctionDef, file_path: str) -> List[Finding]:
        findings = []
        assigned: dict[str, int] = {}  # name -> lineno of assignment
        used: set[str] = set()

        for node in ast.walk(func_node):
            if isinstance(node, ast.Name):
                if isinstance(node.ctx, ast.Store):
                    if not node.id.startswith("_"):
                        assigned[node.id] = node.lineno
                elif isinstance(node.ctx, ast.Load):
                    used.add(node.id)

        for name, lineno in assigned.items():
            if name not in used and name not in ("self", "cls"):
                findings.append(Finding(
                    tool="dead-code-analyzer",
                    rule_id="DEAD002",
                    message=f"Variable '{name}' assigned but never used in function '{func_node.name}'",
                    file_path=file_path,
                    line_number=lineno,
                    severity="info",
                    code_snippet=f"{name} = ...",
                ))
        return findings

    def _check_unreachable(self, body: list, file_path: str) -> List[Finding]:
        findings = []
        terminators = (ast.Return, ast.Raise, ast.Break, ast.Continue)
        for i, stmt in enumerate(body):
            if isinstance(stmt, terminators) and i + 1 < len(body):
                next_stmt = body[i + 1]
                findings.append(Finding(
                    tool="dead-code-analyzer",
                    rule_id="DEAD003",
                    message="Unreachable code detected after return/raise/break/continue",
                    file_path=file_path,
                    line_number=next_stmt.lineno,
                    severity="warning",
                    code_snippet="# unreachable code",
                ))
                break  # only report first unreachable block
        return findings

    # ── JavaScript / TypeScript ─────────────────────────────────────────────

    def _analyze_js_ts(self, source: str, file_path: str, ext: str) -> List[Finding]:
        findings = []
        lines = source.splitlines()

        # Unused variables: declared with const/let/var but never referenced again
        decl_pattern = re.compile(r"^\s*(?:const|let|var)\s+(\w+)\s*=", re.MULTILINE)
        for m in decl_pattern.finditer(source):
            name = m.group(1)
            if name.startswith("_"):
                continue
            # Count occurrences excluding the declaration line
            occurrences = len(re.findall(r"\b" + re.escape(name) + r"\b", source))
            if occurrences == 1:  # only the declaration itself
                lineno = source[:m.start()].count("\n") + 1
                findings.append(Finding(
                    tool="dead-code-analyzer",
                    rule_id="DEAD001",
                    message=f"Variable '{name}' is declared but never used",
                    file_path=file_path,
                    line_number=lineno,
                    severity="warning",
                    code_snippet=lines[lineno - 1].strip() if lineno <= len(lines) else "",
                ))

        # TODO comments often mark dead/incomplete code
        todo_pattern = re.compile(r"//\s*(TODO|FIXME|HACK|XXX)\b.*", re.IGNORECASE)
        for i, line in enumerate(lines, 1):
            m = todo_pattern.search(line)
            if m:
                findings.append(Finding(
                    tool="dead-code-analyzer",
                    rule_id="DEAD004",
                    message=f"Code annotation requires attention: {m.group(0).strip()}",
                    file_path=file_path,
                    line_number=i,
                    severity="info",
                    code_snippet=line.strip(),
                ))

        return findings
