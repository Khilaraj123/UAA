"""Data structures and normalization utilities for UAA specifications."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional
import re

def normalize_path(path: str) -> str:
    """Normalize path parameters from :id, <id>, or {id} into canonical {id} format."""
    p = path.strip()
    if not p.startswith("/"):
        p = "/" + p
    # Convert <param> syntax (Flask, Bottle, e.g. <int:id> or <id>) -> {param}
    p = re.sub(r"<(?:\w+:)?([a-zA-Z_][a-zA-Z0-9_]*)>", r"{\1}", p)
    # Convert :param syntax (Express, Nest, etc.) -> {param}
    p = re.sub(r":([a-zA-Z_][a-zA-Z0-9_]*)", r"{\1}", p)
    # Normalize trailing slash except root
    if len(p) > 1 and p.endswith("/"):
        p = p[:-1]
    return p

def make_endpoint_id(api_type: str, method: str, path: str) -> str:
    """Construct stable canonical endpoint ID."""
    norm_path = normalize_path(path)
    return f"{api_type.lower()}:{method.upper()}:{norm_path}"

@dataclass
class SourceEvidence:
    source_type: str  # contract, framework_route, source_code, plugin_module, runtime_metadata, gateway_config
    file_path: str
    confidence: str = "high"
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    symbol: Optional[str] = None
    snippet: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class Endpoint:
    endpoint_id: str
    api_type: str
    method: str
    path_template: str
    discovery_status: str  # confirmed, inferred, contract_only, runtime_only
    confidence: str        # high, medium, low
    source_evidence: List[SourceEvidence] = field(default_factory=list)
    full_path_if_known: Optional[str] = None
    operation_id: Optional[str] = None
    name: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    request_body: Optional[Dict[str, Any]] = None
    responses: List[Dict[str, Any]] = field(default_factory=list)
    authentication: Dict[str, Any] = field(default_factory=lambda: {"required": False})
    side_effect_risk: str = "unknown"
    tags: List[str] = field(default_factory=list)
    gaps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["source_evidence"] = [e.to_dict() if isinstance(e, SourceEvidence) else e for e in self.source_evidence]
        return d

@dataclass
class Scenario:
    scenario_id: str
    endpoint_id: str
    title: str
    category: str
    priority: str
    request: Dict[str, Any]
    assertions: List[Dict[str, Any]]
    safety: Dict[str, bool]
    enabled: bool = True
    rationale: str = ""
    auth_profile: Optional[str] = None
    preconditions: List[str] = field(default_factory=list)
    cleanup: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    skip_reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
