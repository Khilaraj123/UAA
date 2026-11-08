"""Coverage Ledger Engine for Universal API Assurance (UAA).

Maintains a multi-stage verification ledger tracking:
1. Discovery sources inspected
2. Endpoints discovered
3. Endpoints understood
4. Endpoints with designed scenarios
5. Endpoints executed
6. Verified endpoints vs. unverified
7. Root causes for untested surfaces
"""

import json
import datetime
from typing import Any, Dict, List, Optional

class CoverageLedgerBuilder:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.sources: List[Dict[str, Any]] = []
        self.endpoints_ledger: Dict[str, Dict[str, Any]] = {}
        self.unverified_endpoints: List[Dict[str, Any]] = []

    def record_source(
        self,
        name: str,
        layer: int,
        status: str,
        files_scanned: int = 0,
        endpoints_yielded: int = 0,
        notes: str = "",
    ) -> None:
        self.sources.append({
            "source_name": name,
            "layer": layer,
            "status": status,
            "files_scanned": files_scanned,
            "endpoints_yielded": endpoints_yielded,
            "limitation_notes": notes,
        })

    def record_discovery(
        self,
        endpoint_id: str,
        method: str,
        path: str,
        status: str = "confirmed",
        sources: Optional[List[str]] = None,
    ) -> None:
        if endpoint_id not in self.endpoints_ledger:
            self.endpoints_ledger[endpoint_id] = {
                "endpoint_id": endpoint_id,
                "method": method,
                "path": path,
                "stage_discovery": {"status": status, "sources": sources or []},
                "stage_understanding": {
                    "status": "not_analyzed",
                    "auth_mapped": False,
                    "params_mapped": False,
                    "side_effects_classified": False,
                },
                "stage_scenarios_designed": {
                    "scenario_count": 0,
                    "categories": [],
                },
                "stage_executed": {
                    "executed_count": 0,
                    "passed_count": 0,
                    "failed_count": 0,
                    "skipped_count": 0,
                },
                "stage_verified": False,
                "untested_reason": None,
            }
        else:
            self.endpoints_ledger[endpoint_id]["stage_discovery"] = {
                "status": status,
                "sources": sources or [],
            }

    def record_understanding(
        self,
        endpoint_id: str,
        status: str = "complete",
        auth_mapped: bool = True,
        params_mapped: bool = True,
        side_effects_classified: bool = True,
    ) -> None:
        if endpoint_id in self.endpoints_ledger:
            self.endpoints_ledger[endpoint_id]["stage_understanding"] = {
                "status": status,
                "auth_mapped": auth_mapped,
                "params_mapped": params_mapped,
                "side_effects_classified": side_effects_classified,
            }

    def record_scenarios(
        self,
        endpoint_id: str,
        scenario_count: int,
        categories: List[str],
    ) -> None:
        if endpoint_id in self.endpoints_ledger:
            self.endpoints_ledger[endpoint_id]["stage_scenarios_designed"] = {
                "scenario_count": scenario_count,
                "categories": sorted(list(set(categories))),
            }

    def record_execution(
        self,
        endpoint_id: str,
        executed: int,
        passed: int,
        failed: int,
        skipped: int,
        untested_reason: Optional[str] = None,
    ) -> None:
        if endpoint_id in self.endpoints_ledger:
            entry = self.endpoints_ledger[endpoint_id]
            entry["stage_executed"] = {
                "executed_count": executed,
                "passed_count": passed,
                "failed_count": failed,
                "skipped_count": skipped,
            }
            # Verified if at least one passed and zero failed
            is_verified = (passed > 0 and failed == 0)
            entry["stage_verified"] = is_verified
            if not is_verified:
                entry["untested_reason"] = untested_reason or ("failures_present" if failed > 0 else "not_executed")
                self.unverified_endpoints.append({
                    "endpoint_id": endpoint_id,
                    "reason": entry["untested_reason"],
                    "remediation_to_test": f"Resolve {entry['untested_reason']} to achieve verification.",
                })
            else:
                entry["untested_reason"] = None

    def build(self) -> Dict[str, Any]:
        endpoints = list(self.endpoints_ledger.values())
        total_discovered = len(endpoints)
        understood = sum(1 for e in endpoints if e["stage_understanding"]["status"] == "complete")
        with_scenarios = sum(1 for e in endpoints if e["stage_scenarios_designed"]["scenario_count"] > 0)
        executed = sum(1 for e in endpoints if e["stage_executed"]["executed_count"] > 0)
        verified = sum(1 for e in endpoints if e["stage_verified"])
        unverified = total_discovered - verified
        ratio = round(verified / total_discovered, 4) if total_discovered > 0 else 0.0

        return {
            "schema_version": "2.0.0",
            "run_id": self.run_id,
            "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "sources_inspected": self.sources,
            "metrics": {
                "total_endpoints_discovered": total_discovered,
                "endpoints_understood": understood,
                "endpoints_with_scenarios": with_scenarios,
                "endpoints_executed": executed,
                "endpoints_verified_pass": verified,
                "endpoints_unverified": unverified,
                "coverage_ratio": ratio,
            },
            "endpoint_ledger": endpoints,
            "unverified_endpoints": self.unverified_endpoints,
        }

    def to_markdown(self) -> str:
        data = self.build()
        m = data["metrics"]
        lines = [
            f"# UAA Measurable Coverage Ledger - Run `{self.run_id}`",
            "",
            "## Verification Progression Metrics",
            "",
            f"- **Discovered Endpoints**: {m['total_endpoints_discovered']}",
            f"- **Understood**: {m['endpoints_understood']} ({(m['endpoints_understood']/m['total_endpoints_discovered']*100) if m['total_endpoints_discovered'] else 0:.1f}%)",
            f"- **With Scenarios**: {m['endpoints_with_scenarios']} ({(m['endpoints_with_scenarios']/m['total_endpoints_discovered']*100) if m['total_endpoints_discovered'] else 0:.1f}%)",
            f"- **Executed**: {m['endpoints_executed']} ({(m['endpoints_executed']/m['total_endpoints_discovered']*100) if m['total_endpoints_discovered'] else 0:.1f}%)",
            f"- **Verified (Passing)**: {m['endpoints_verified_pass']} ({m['coverage_ratio']*100:.1f}%)",
            f"- **Unverified Remaining**: {m['endpoints_unverified']}",
            "",
            "## Inspected Discovery Sources",
            "",
            "| Layer | Source Name | Status | Files Scanned | Endpoints Yielded | Limitation Notes |",
            "|---|---|---|---|---|---|",
        ]
        for s in data["sources_inspected"]:
            lines.append(f"| {s['layer']} | `{s['source_name']}` | {s['status']} | {s['files_scanned']} | {s['endpoints_yielded']} | {s['limitation_notes']} |")

        lines.extend([
            "",
            "## Endpoint Verification Matrix",
            "",
            "| Endpoint | Discovered | Understood | Scenarios | Executed (P/F/S) | Verified | Untested Reason |",
            "|---|---|---|---|---|---|---|",
        ])
        for e in data["endpoint_ledger"]:
            disc = "✅ " + e["stage_discovery"]["status"]
            und = "✅" if e["stage_understanding"]["status"] == "complete" else "⚠️"
            scen = str(e["stage_scenarios_designed"]["scenario_count"])
            ex = e["stage_executed"]
            ex_str = f"{ex['executed_count']} ({ex['passed_count']}/{ex['failed_count']}/{ex['skipped_count']})"
            ver = "✅ VERIFIED" if e["stage_verified"] else "❌ UNVERIFIED"
            reason = e["untested_reason"] or "-"
            lines.append(f"| `{e['method']} {e['path']}` | {disc} | {und} | {scen} | {ex_str} | {ver} | {reason} |")

        if data["unverified_endpoints"]:
            lines.extend([
                "",
                "## Actionable Remediation for Unverified Endpoints",
                "",
                "| Endpoint ID | Reason | Action Required |",
                "|---|---|---|",
            ])
            for u in data["unverified_endpoints"]:
                lines.append(f"| `{u['endpoint_id']}` | `{u['reason']}` | {u['remediation_to_test']} |")

        return "\n".join(lines)

