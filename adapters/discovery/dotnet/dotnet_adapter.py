"""ASP.NET Core discovery adapter for C# controllers and Minimal APIs."""

import re
from pathlib import Path
from typing import List
from adapters.discovery.base import BaseDiscoveryAdapter
from engine.specification.models import Endpoint, SourceEvidence, make_endpoint_id, normalize_path

CONTROLLER_ROUTE_PATTERN = re.compile(r"""\[Route\s*\(\s*["']([^"']+)["']\s*\)\]""", re.IGNORECASE)
ACTION_METHOD_PATTERN = re.compile(r"""\[Http(Get|Post|Put|Delete|Patch|Head|Options)\s*(?:\(\s*["']([^"']*)["']\s*\))?\]""", re.IGNORECASE)
MINIMAL_API_PATTERN = re.compile(r"""(?:app|group)\.Map(Get|Post|Put|Delete|Patch)\s*\(\s*["']([^"']+)["']""", re.IGNORECASE)

class DotNetDiscoveryAdapter(BaseDiscoveryAdapter):
    @property
    def name(self) -> str:
        return "dotnet"

    def detect(self, repo_path: Path) -> bool:
        return any(repo_path.rglob("*.csproj")) or any(repo_path.rglob("*.sln"))

    def discover(self, repo_path: Path) -> List[Endpoint]:
        endpoints: List[Endpoint] = []
        for cs_file in repo_path.rglob("*.cs"):
            if any(p in cs_file.parts for p in ("bin", "obj", ".git")):
                continue
            try:
                content = cs_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            rel_path = str(cs_file.relative_to(repo_path)).replace("\\", "/")
            lines = content.splitlines()

            # 1. Parse Minimal APIs
            for i, line in enumerate(lines, 1):
                min_match = MINIMAL_API_PATTERN.search(line)
                if min_match:
                    method = min_match.group(1).upper()
                    raw_path = min_match.group(2)
                    norm_path = normalize_path(raw_path)
                    ep_id = make_endpoint_id("rest", method, norm_path)
                    has_auth = "RequireAuthorization" in line or "[Authorize]" in line

                    endpoints.append(Endpoint(
                        endpoint_id=ep_id,
                        api_type="rest",
                        method=method,
                        path_template=norm_path,
                        discovery_status="confirmed",
                        confidence="high",
                        source_evidence=[SourceEvidence(
                            source_type="framework_route",
                            file_path=rel_path,
                            line_start=i,
                            line_end=i,
                            snippet=line.strip(),
                            confidence="high",
                        )],
                        authentication={"required": has_auth},
                        side_effect_risk="read" if method in ("GET", "HEAD") else "reversible_write",
                        tags=["aspnetcore", "minimal-api"],
                    ))

            # 2. Parse Controller actions
            controller_prefix = ""
            for i, line in enumerate(lines, 1):
                route_match = CONTROLLER_ROUTE_PATTERN.search(line)
                if route_match:
                    controller_prefix = route_match.group(1).replace("[controller]", cs_file.stem.replace("Controller", "").lower())

                act_match = ACTION_METHOD_PATTERN.search(line)
                if act_match:
                    method = act_match.group(1).upper()
                    action_subpath = act_match.group(2) or ""
                    full_path = f"/{controller_prefix.strip('/')}/{action_subpath.strip('/')}".rstrip("/")
                    if not full_path:
                        full_path = "/"
                    norm_path = normalize_path(full_path)
                    ep_id = make_endpoint_id("rest", method, norm_path)

                    endpoints.append(Endpoint(
                        endpoint_id=ep_id,
                        api_type="rest",
                        method=method,
                        path_template=norm_path,
                        discovery_status="confirmed",
                        confidence="high",
                        source_evidence=[SourceEvidence(
                            source_type="framework_route",
                            file_path=rel_path,
                            line_start=i,
                            line_end=i,
                            snippet=line.strip(),
                            confidence="high",
                        )],
                        authentication={"required": "[Authorize]" in content},
                        side_effect_risk="read" if method in ("GET", "HEAD") else "reversible_write",
                        tags=["aspnetcore", "controller"],
                    ))

        return endpoints

