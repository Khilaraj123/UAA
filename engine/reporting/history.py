"""Historical run storage and regression analysis for UAA."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import os
import shutil

class RunHistoryManager:
    """Manages sequential audit runs in api-audit/runs/run-XXX/ and detects regressions."""

    def __init__(self, base_audit_dir: str = "api-audit"):
        self.base_dir = Path(base_audit_dir)
        self.runs_dir = self.base_dir / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def get_next_run_id(self) -> str:
        """Calculate next run ID (e.g., run-001, run-002)."""
        existing = [d for d in self.runs_dir.iterdir() if d.is_dir() and d.name.startswith("run-")]
        if not existing:
            return "run-001"
        indices = []
        for d in existing:
            parts = d.name.split("-")
            if len(parts) == 2 and parts[1].isdigit():
                indices.append(int(parts[1]))
        next_idx = (max(indices) + 1) if indices else 1
        return f"run-{next_idx:03d}"

    def get_run_dir(self, run_id: str) -> Path:
        d = self.runs_dir / run_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def list_runs(self) -> List[str]:
        """Return sorted list of run IDs."""
        dirs = [d.name for d in self.runs_dir.iterdir() if d.is_dir() and d.name.startswith("run-")]
        dirs.sort()
        return dirs

    def load_run_artifact(self, run_id: str, artifact_name: str) -> Optional[Dict[str, Any]]:
        path = self.runs_dir / run_id / artifact_name
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    def save_run_artifact(self, run_id: str, artifact_name: str, data: Any) -> Path:
        run_dir = self.get_run_dir(run_id)
        out_path = run_dir / artifact_name
        with open(out_path, "w", encoding="utf-8") as f:
            if isinstance(data, (dict, list)):
                json.dump(data, f, indent=2)
            else:
                f.write(str(data))
        return out_path

    def compare_runs(self, previous_run_id: str, current_run_id: str) -> Dict[str, Any]:
        """Compare two runs for regressions, fixes, and endpoint drift."""
        prev_exec = self.load_run_artifact(previous_run_id, "execution-results.json")
        curr_exec = self.load_run_artifact(current_run_id, "execution-results.json")

        if not prev_exec or not curr_exec:
            return {
                "status": "unavailable",
                "message": "One or both runs lack execution-results.json",
                "regressions": [],
                "fixes": [],
                "missing_scenarios": [],
                "new_scenarios": [],
                "regression_count": 0,
                "fix_count": 0,
                "missing_scenario_count": 0,
                "new_scenario_count": 0,
            }

        prev_results = {r["scenario_id"]: r for r in prev_exec.get("results", [])}
        curr_results = {r["scenario_id"]: r for r in curr_exec.get("results", [])}

        regressions = []
        fixes = []
        unchanged_passing = 0
        unchanged_failing = 0
        new_scenarios = []
        missing_scenarios = []

        # Check all scenarios in current run
        for scen_id, curr_res in curr_results.items():
            curr_passed = curr_res.get("passed", False)
            if scen_id in prev_results:
                prev_res = prev_results[scen_id]
                prev_passed = prev_res.get("passed", False)

                if prev_passed and not curr_passed:
                    regressions.append({
                        "scenario_id": scen_id,
                        "endpoint_id": curr_res.get("endpoint_id"),
                        "type": "status_regression",
                        "message": f"Scenario {scen_id} previously PASSED in {previous_run_id} but now FAILED in {current_run_id}",
                    })
                elif not prev_passed and curr_passed:
                    fixes.append({
                        "scenario_id": scen_id,
                        "endpoint_id": curr_res.get("endpoint_id"),
                        "type": "status_fix",
                        "message": f"Scenario {scen_id} previously FAILED in {previous_run_id} but now PASSED in {current_run_id}",
                    })
                elif curr_passed:
                    unchanged_passing += 1
                else:
                    unchanged_failing += 1
            else:
                # Scenario is new in current run
                new_entry = {
                    "scenario_id": scen_id,
                    "endpoint_id": curr_res.get("endpoint_id"),
                    "type": "new_scenario",
                    "passed": curr_passed,
                    "message": f"New scenario {scen_id} introduced in {current_run_id} ({'PASSED' if curr_passed else 'FAILED'})",
                }
                new_scenarios.append(new_entry)
                if not curr_passed:
                    regressions.append({
                        "scenario_id": scen_id,
                        "endpoint_id": curr_res.get("endpoint_id"),
                        "type": "new_failure",
                        "message": f"New scenario {scen_id} introduced in {current_run_id} FAILED",
                    })

        # Check scenarios that existed previously but are missing in current run
        for scen_id, prev_res in prev_results.items():
            if scen_id not in curr_results:
                prev_passed = prev_res.get("passed", False)
                msg = (
                    f"Scenario {scen_id} previously PASSED in {previous_run_id} but is MISSING in {current_run_id} (coverage loss)"
                    if prev_passed
                    else f"Scenario {scen_id} existed in {previous_run_id} (FAILED) but is MISSING in {current_run_id} (coverage loss)"
                )
                missing_entry = {
                    "scenario_id": scen_id,
                    "endpoint_id": prev_res.get("endpoint_id"),
                    "type": "coverage_loss",
                    "previously_passed": prev_passed,
                    "message": msg,
                }
                missing_scenarios.append(missing_entry)
                regressions.append(missing_entry)

        prev_sum = prev_exec.get("summary", {})
        curr_sum = curr_exec.get("summary", {})

        return {
            "status": "compared",
            "previous_run_id": previous_run_id,
            "current_run_id": current_run_id,
            "pass_rate_previous": prev_sum.get("pass_rate", 0.0),
            "pass_rate_current": curr_sum.get("pass_rate", 0.0),
            "pass_rate_delta": round(curr_sum.get("pass_rate", 0.0) - prev_sum.get("pass_rate", 0.0), 2),
            "regressions": regressions,
            "fixes": fixes,
            "missing_scenarios": missing_scenarios,
            "new_scenarios": new_scenarios,
            "regression_count": len(regressions),
            "fix_count": len(fixes),
            "missing_scenario_count": len(missing_scenarios),
            "new_scenario_count": len(new_scenarios),
            "unchanged_passing": unchanged_passing,
            "unchanged_failing": unchanged_failing,
        }

