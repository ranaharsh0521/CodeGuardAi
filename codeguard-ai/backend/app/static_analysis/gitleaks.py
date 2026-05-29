import json
import subprocess
import os
import tempfile
from typing import List
from app.core.config import settings
from app.schemas.analysis import Finding

class GitleaksScanner:
    def __init__(self):
        # Assumes gitleaks is installed in the environment
        self.cmd = "gitleaks"
        
    def scan_directory(self, path: str) -> List[Finding]:
        findings = []
        try:
            # Check if gitleaks is available
            result = subprocess.run([self.cmd, "version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Gitleaks not available, skipping secret scan")
                return self._create_demo_findings(path) if settings.ENABLE_DEMO_FINDINGS else []
                
            # Gitleaks outputs to a file, so we create a temp file
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                report_path = tmp.name
                
            # Run gitleaks detect
            result = subprocess.run(
                [self.cmd, "detect", "--source", path, "--report-path", report_path, "--report-format", "json", "--no-git"],
                capture_output=True,
                text=True,
                timeout=60  # Add timeout
            )
            
            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                with open(report_path, "r") as f:
                    data = json.load(f)
                    
                for result_item in data:
                    finding = Finding(
                        tool="gitleaks",
                        rule_id=result_item.get("RuleID", "secret-detected"),
                        message=result_item.get("Description", "Potential secret found"),
                        file_path=result_item.get("File", ""),
                        line_number=result_item.get("StartLine", 0),
                        severity="critical",  # secrets are almost always critical
                        code_snippet=result_item.get("Match", "")
                    )
                    findings.append(finding)

            if os.path.exists(report_path):
                os.remove(report_path)

            if settings.ENABLE_DEMO_FINDINGS and not findings:
                return self._create_demo_findings(path)
                
        except Exception as e:
            print(f"Gitleaks execution failed: {str(e)}")
            return self._create_demo_findings(path) if settings.ENABLE_DEMO_FINDINGS else []
            
        return findings
    
    def _create_demo_findings(self, path: str) -> List[Finding]:
        """Create demo findings when gitleaks is not available"""
        return [
            Finding(
                tool="gitleaks",
                rule_id="generic-api-key",
                message="Generic API Key detected",
                file_path=os.path.join(path, "config.py"),
                line_number=8,
                severity="critical",
                code_snippet="SECRET_KEY = 'sk-1234567890abcdef1234567890abcdef'"
            )
        ]
