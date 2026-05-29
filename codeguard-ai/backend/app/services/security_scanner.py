from typing import List
from app.schemas.analysis import Finding
from app.static_analysis.semgrep import SemgrepScanner

class SecurityScanner:
    def __init__(self):
        self.scanner = SemgrepScanner()
        
    def scan(self, directory_path: str) -> List[Finding]:
        """
        Runs Semgrep on the given directory and returns findings.
        """
        findings = self.scanner.scan_directory(directory_path)
        return findings
