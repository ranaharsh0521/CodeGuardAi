"""
Quality Gates — evaluate scan results against configurable thresholds.
Returns a pass/fail status with detailed gate breakdown.
"""
from typing import List, Dict, Any
from app.schemas.analysis import Finding


DEFAULT_GATES = {
    "max_critical": 0,       # Zero tolerance for critical findings
    "max_high": 5,           # At most 5 high-severity
    "max_risk_score": 70,    # Risk score must be ≤ 70
    "max_duplicates": 20,    # At most 20 duplicate code findings
    "max_dead_code": 30,     # At most 30 dead code findings
    "max_secrets": 0,        # Zero tolerance for secrets
}


class QualityGates:
    def __init__(self, gates: Dict[str, int] | None = None):
        self.gates = gates or DEFAULT_GATES

    def evaluate(self, findings: List[Finding], risk_score: int) -> Dict[str, Any]:
        """
        Evaluate findings against quality gates.
        Returns:
            {
                "passed": bool,
                "gates": [
                    {"name": str, "threshold": int, "actual": int, "passed": bool}
                ],
                "summary": str
            }
        """
        counts = self._count_findings(findings)
        gate_results = []

        checks = [
            ("Critical Issues", "max_critical", counts["critical"]),
            ("Secret / API Keys", "max_secrets", counts["secrets"]),
            ("High Severity Issues", "max_high", counts["high"]),
            ("Risk Score", "max_risk_score", risk_score),
            ("Duplicate Code Blocks", "max_duplicates", counts["duplicates"]),
            ("Dead Code Issues", "max_dead_code", counts["dead_code"]),
        ]

        all_passed = True
        for name, gate_key, actual in checks:
            threshold = self.gates.get(gate_key, 9999)
            passed = actual <= threshold
            if not passed:
                all_passed = False
            gate_results.append({
                "name": name,
                "threshold": threshold,
                "actual": actual,
                "passed": passed,
                "gate_key": gate_key,
            })

        summary = "All quality gates passed ✓" if all_passed else (
            f"{sum(1 for g in gate_results if not g['passed'])} gate(s) failed — merge blocked"
        )

        return {
            "passed": all_passed,
            "gates": gate_results,
            "summary": summary,
            "risk_score": risk_score,
        }

    def _count_findings(self, findings: List[Finding]) -> Dict[str, int]:
        counts = {
            "critical": 0,
            "high": 0,
            "secrets": 0,
            "duplicates": 0,
            "dead_code": 0,
        }
        for f in findings:
            sev = f.severity.lower()
            if sev == "critical":
                counts["critical"] += 1
            elif sev in ("error", "high"):
                counts["high"] += 1
            if f.tool in ("secret-detector", "gitleaks"):
                counts["secrets"] += 1
            if f.tool == "duplicate-code-analyzer":
                counts["duplicates"] += 1
            if f.tool == "dead-code-analyzer":
                counts["dead_code"] += 1
        return counts
