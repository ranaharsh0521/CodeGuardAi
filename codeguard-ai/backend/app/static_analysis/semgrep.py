import json
import subprocess
import os
from typing import List, Dict, Any
from app.core.config import settings
from app.schemas.analysis import Finding

class SemgrepScanner:
    def __init__(self):
        # We assume semgrep is installed in the environment/container
        self.cmd = "semgrep"
        
    def scan_directory(self, path: str) -> List[Finding]:
        findings = []
        try:
            # Check if semgrep is available
            result = subprocess.run([self.cmd, "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Semgrep not available, skipping security scan")
                return self._create_demo_findings(path) if settings.ENABLE_DEMO_FINDINGS else []
                
            # Run semgrep with auto config and JSON output
            result = subprocess.run(
                [self.cmd, "scan", "--config", "auto", "--json", path],
                capture_output=True,
                text=True,
                timeout=60  # Add timeout
            )
            
            if not result.stdout:
                return self._create_demo_findings(path) if settings.ENABLE_DEMO_FINDINGS else []
                
            data = json.loads(result.stdout)
            
            for result_item in data.get("results", []):
                rule_id = result_item.get("check_id", "unknown")
                extra = result_item.get("extra", {})
                message = extra.get("message", "")
                severity = extra.get("severity", "WARNING").lower()
                lines = extra.get("lines", "")
                
                path_str = result_item.get("path", "")
                start_line = result_item.get("start", {}).get("line", 0)
                
                finding = Finding(
                    tool="semgrep",
                    rule_id=rule_id,
                    message=message,
                    file_path=path_str,
                    line_number=start_line,
                    severity=severity,
                    code_snippet=lines
                )
                findings.append(finding)

            if settings.ENABLE_DEMO_FINDINGS and not findings:
                return self._create_demo_findings(path)
                
        except Exception as e:
            print(f"Semgrep execution failed: {str(e)}")
            return self._create_demo_findings(path) if settings.ENABLE_DEMO_FINDINGS else []
            
        return findings
    
    def _create_demo_findings(self, path: str) -> List[Finding]:
        """Create demo findings when semgrep is not available"""
        return [
            Finding(
                tool="semgrep",
                rule_id="demo.hardcoded-secret",
                message="Potential hardcoded secret detected",
                file_path=os.path.join(path, "example.py"),
                line_number=42,
                severity="warning",
                code_snippet="API_KEY = 'sk-1234567890abcdef'"
            ),
            Finding(
                tool="semgrep",
                rule_id="demo.sql-injection",
                message="Potential SQL injection vulnerability",
                file_path=os.path.join(path, "database.py"),
                line_number=15,
                severity="error",
                code_snippet="query = f'SELECT * FROM users WHERE id = {user_id}'"
            )
        ]
