"""Evidence collection, provenance tracking, and grounding for UAA."""

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import datetime

CLAIM_TYPES = ("documented", "observed", "inferred", "unknown")
CONFIDENCE_LEVELS = ("high", "medium", "low")

@dataclass
class EvidenceAnchor:
    source_layer: int  # 1 to 6
    source_type: str   # contract, framework_route, source_code, plugin, runtime, gateway
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol: Optional[str] = None
    snippet: Optional[str] = None
    confidence: str = "high"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class EvidenceRecord:
    evidence_id: str
    target_id: str  # endpoint_id, finding_id, or scenario_id
    claim: str
    claim_type: str  # documented, observed, inferred, unknown
    confidence: str  # high, medium, low
    anchors: List[EvidenceAnchor] = field(default_factory=list)
    recorded_at: str = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc).isoformat())
    agent_id: Optional[str] = None
    reviewed_by: Optional[str] = None
    review_verdict: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["anchors"] = [a.to_dict() if isinstance(a, EvidenceAnchor) else a for a in self.anchors]
        return d

class EvidenceLedger:
    """Manages traceable evidence records for an audit run."""

    def __init__(self):
        self.records: Dict[str, EvidenceRecord] = {}

    def add_record(
        self,
        evidence_id: str,
        target_id: str,
        claim: str,
        claim_type: str,
        confidence: str = "high",
        anchors: Optional[List[EvidenceAnchor]] = None,
        agent_id: Optional[str] = None,
    ) -> EvidenceRecord:
        if claim_type not in CLAIM_TYPES:
            raise ValueError(f"Invalid claim_type '{claim_type}'. Must be one of {CLAIM_TYPES}")
        if confidence not in CONFIDENCE_LEVELS:
            raise ValueError(f"Invalid confidence '{confidence}'. Must be one of {CONFIDENCE_LEVELS}")

        rec = EvidenceRecord(
            evidence_id=evidence_id,
            target_id=target_id,
            claim=claim,
            claim_type=claim_type,
            confidence=confidence,
            anchors=anchors or [],
            agent_id=agent_id,
        )
        self.records[evidence_id] = rec
        return rec

    def review_record(self, evidence_id: str, reviewer: str, verdict: str) -> None:
        if evidence_id in self.records:
            self.records[evidence_id].reviewed_by = reviewer
            self.records[evidence_id].review_verdict = verdict

    def get_for_target(self, target_id: str) -> List[EvidenceRecord]:
        return [r for r in self.records.values() if r.target_id == target_id]

    def to_dict(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self.records.values()]

