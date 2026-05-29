from typing import List, Dict, Any
from app.schemas.analysis import Finding
from app.services.security_scanner import SecurityScanner
from app.services.secret_detector import SecretDetector
from app.services.fallback_scanner import FallbackScanner
from app.services.dependency_scanner import DependencyScanner
from app.services.dead_code_analyzer import DeadCodeAnalyzer
from app.services.duplicate_code_analyzer import DuplicateCodeAnalyzer
from app.services.quality_gates import QualityGates
from app.services.ai_suggester import AISuggester
import asyncio


class AnalyzerService:
    def __init__(self):
        self.security_scanner = SecurityScanner()
        self.secret_detector = SecretDetector()
        self.fallback_scanner = FallbackScanner()
        self.dependency_scanner = DependencyScanner()
        self.dead_code_analyzer = DeadCodeAnalyzer()
        self.duplicate_code_analyzer = DuplicateCodeAnalyzer()
        self.quality_gates = QualityGates()
        self.ai_suggester = AISuggester()

    def run_full_analysis(self, directory_path: str) -> List[Finding]:
        findings: List[Finding] = []

        # Run the external tool-based scanners first.  Each one falls back to
        # demo findings or returns [] if the tool is not installed.
        findings.extend(self.security_scanner.scan(directory_path))
        findings.extend(self.secret_detector.detect(directory_path))

        # Always run the pure-Python fallback scanner in addition to (not
        # instead of) the external tools.  It never requires installation and
        # catches common patterns the demo fixtures don't cover.
        fallback_findings = self.fallback_scanner.scan(directory_path)
        # Avoid exact duplicates on the same file+line from the fallback scanner
        # and any demo findings that the external scanners may have injected.
        existing_keys = {(f.file_path, f.line_number, f.rule_id) for f in findings}
        for f in fallback_findings:
            key = (f.file_path, f.line_number, f.rule_id)
            if key not in existing_keys:
                findings.append(f)
                existing_keys.add(key)

        findings.extend(self.dependency_scanner.scan(directory_path))
        findings.extend(self.dead_code_analyzer.scan(directory_path))
        findings.extend(self.duplicate_code_analyzer.scan(directory_path))

        return [self._enhance_with_ai(f) for f in findings]

    def run_quality_gates(self, findings: List[Finding], risk_score: int) -> Dict[str, Any]:
        """Evaluate scan results against quality gates. Returns gate report."""
        return self.quality_gates.evaluate(findings, risk_score)

    def _enhance_with_ai(self, finding: Finding) -> Finding:
        """Enhance finding with AI suggestions — safe sync wrapper."""
        if not self.ai_suggester.api_key:
            return finding
        # Guard: AI_API_KEY is a placeholder string in the example .env.
        placeholder = "REPLACE_WITH_YOUR"
        if self.ai_suggester.api_key.startswith(placeholder):
            return finding
        try:
            finding_dict = finding.model_dump()
            # asyncio.run() works here because this method is called from
            # asyncio.to_thread() which runs in a plain OS thread (no running
            # event loop in the thread itself).
            ai_result = asyncio.run(
                self.ai_suggester.get_fix_suggestion(finding_dict)
            )
            finding.ai_explanation = ai_result.get("ai_explanation")
            finding.ai_fix_suggestion = ai_result.get("ai_fix_suggestion")
        except Exception as e:
            print(f"AI enhancement skipped: {e}")
        return finding

    def calculate_risk_score(self, findings: List[Finding]) -> int:
        weights = {"critical": 10, "error": 5, "high": 5, "warning": 2, "info": 1}
        score = sum(weights.get(f.severity.lower(), 1) for f in findings)
        return min(score, 100)
