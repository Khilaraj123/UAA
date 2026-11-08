"""Security and correctness finding models for UAA."""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json

SEVERITIES = ("critical", "high", "medium", "low", "info")
CATEGORIES = (
    "bola_idor",
    "broken_authentication",
    "broken_authorization",
    "mass_assignment",
    "injection",
    "rate_limiting",
    "data_exposure",
    "contract_mismatch",
    "unhandled_exception",
    "security_misconfiguration",
)

@dataclass
class Finding:
    finding_id: str
    title: str
    severity: str
    category: str
    endpoint_id: str
    status: str
    description: str
    impact: str
    evidence: Dict[str, Any]
    remediation: Dict[str, Any]
    cwe_id: Optional[str] = None
    owasp_api_category: Optional[str] = None
    independent_review: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class FindingStore:
    """Manages security and correctness findings for an audit run."""

    def __init__(self):
        self.findings: Dict[str, Finding] = {}

    def add_finding(self, finding: Finding) -> None:
        if finding.severity not in SEVERITIES:
            raise ValueError(f"Invalid severity '{finding.severity}'. Must be in {SEVERITIES}")
        if finding.category not in CATEGORIES:
            raise ValueError(f"Invalid category '{finding.category}'. Must be in {CATEGORIES}")
        self.findings[finding.finding_id] = finding

    def attach_review(self, finding_id: str, reviewer_role: str, verdict: str, notes: str = "") -> None:
        if finding_id in self.findings:
            self.findings[finding_id].independent_review = {
                "reviewed": True,
                "reviewer_role": reviewer_role,
                "verdict": verdict,
                "notes": notes,
            }

    def list_all(self) -> List[Dict[str, Any]]:
        return [f.to_dict() for f in self.findings.values()]

    def to_markdown(self) -> str:
        lines = [
            "# UAA Security Audit Findings",
            "",
            f"Total Findings: {len(self.findings)}",
            "",
            "| ID | Severity | Category | Endpoint | Title | Status | Reviewed |",
            "|---|---|---|---|---|---|---|",
        ]
        for f in self.findings.values():
            rev = "✅ " + f.independent_review["verdict"] if f.independent_review else "⏳ Pending"
            sev_badge = f"**{f.severity.upper()}**"
            lines.append(
                f"| `{f.finding_id}` | {sev_badge} | `{f.category}` | `{f.endpoint_id}` | {f.title} | `{f.status}` | {rev} |"
            )

        lines.append("")
        for f in self.findings.values():
            lines.extend([
                f"### [{f.severity.upper()}] {f.title} (`{f.finding_id}`)",
                f"- **Endpoint**: `{f.endpoint_id}`",
                f"- **Category**: `{f.category}` | **CWE**: `{f.cwe_id or 'N/A'}` | **OWASP**: `{f.owasp_api_category or 'N/A'}`",
                f"- **Description**: {f.description}",
                f"- **Impact**: {f.impact}",
                "- **Evidence**:",
                f"  - Claim type: `{f.evidence.get('claim_type')}`",
                f"  - Explanation: {f.evidence.get('explanation')}",
                "- **Remediation**:",
                f"  - {f.remediation.get('guidance')}",
                "",
            ])
            if f.remediation.get("suggested_diff"):
                lines.extend([
                    "```diff",
                    f.remediation["suggested_diff"],
                    "```",
                    "",
                ])
        return "\n".join(lines)

