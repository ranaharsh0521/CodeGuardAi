from typing import List
from app.schemas.analysis import Finding
from app.static_analysis.gitleaks import GitleaksScanner

class SecretDetector:
    def __init__(self):
        self.scanner = GitleaksScanner()
        
    def detect(self, directory_path: str) -> List[Finding]:
        """
        Runs Gitleaks on the given directory and returns found secrets.
        """
        findings = self.scanner.scan_directory(directory_path)
        return findings
