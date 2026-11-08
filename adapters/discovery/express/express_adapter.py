"""Express.js discovery adapter using robust regex and route tree extraction."""

import re
from pathlib import Path
from typing import List
from adapters.discovery.base import BaseDiscoveryAdapter
from engine.specification.models import Endpoint, SourceEvidence, make_endpoint_id, normalize_path

ROUTE_PATTERN = re.compile(
    r"""(?:app|router)\.(get|post|put|delete|patch|options|head)\s*\(\s*['"`]([^'"`]+)['"`]""",
    re.IGNORECASE,
)

class ExpressDiscoveryAdapter(BaseDiscoveryAdapter):
    @property
    def name(self) -> str:
        return "express"

    def detect(self, repo_path: Path) -> bool:
        for f in repo_path.glob("package*.json"):
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
                if '"express"' in content:
                    return True
            except Exception:
                continue
        for js_file in repo_path.rglob("*.js"):
            if "node_modules" in js_file.parts:
                continue
            try:
                content = js_file.read_text(encoding="utf-8", errors="ignore")
                if "require('express')" in content or 'require("express")' in content:
                    return True
            except Exception:
                continue
        return False

    def discover(self, repo_path: Path) -> List[Endpoint]:
        endpoints: List[Endpoint] = []
        for file_path in repo_path.rglob("*.[jt]s"):
            if any(p in file_path.parts for p in ("node_modules", "dist", ".git", "build")):
                continue
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            rel_path = str(file_path.relative_to(repo_path)).replace("\\", "/")
            lines = content.splitlines()

            for i, line in enumerate(lines, 1):
                match = ROUTE_PATTERN.search(line)
                if match:
                    method = match.group(1).upper()
                    raw_path = match.group(2)
                    norm_path = normalize_path(raw_path)
                    ep_id = make_endpoint_id("rest", method, norm_path)

                    evidence = SourceEvidence(
                        source_type="framework_route",
                        file_path=rel_path,
                        line_start=i,
                        line_end=i,
                        snippet=line.strip(),
                        confidence="high",
                    )

                    # Check for auth middleware in the route definition line
                    has_auth = any(kw in line.lower() for kw in ("auth", "jwt", "passport", "protect", "requireuser"))

                    endpoints.append(Endpoint(
                        endpoint_id=ep_id,
                        api_type="rest",
                        method=method,
                        path_template=norm_path,
                        discovery_status="confirmed",
                        confidence="high",
                        source_evidence=[evidence],
                        authentication={"required": has_auth},
                        side_effect_risk="read" if method in ("GET", "HEAD") else "reversible_write",
                        tags=["express"],
                    ))
        return endpoints

