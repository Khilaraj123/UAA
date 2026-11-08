"""Universal API Assurance (UAA) Command Line Interface.

Usage:
  python -m engine.cli validate [inventory|testspec|execution|ledger] --file <path>
  python -m engine.cli execute --spec <path> --base-url <url> [--out-dir <dir>] [--allow-destructive]
  python -m engine.cli coverage --inventory <path> --results <path> [--out-dir <dir>]
  python -m engine.cli security-check --inventory <path> [--results <path>] [--out-dir <dir>]
  python -m engine.cli report --run-dir <dir>
  python -m engine.cli history-compare --runs-dir <dir> --prev <run-id> --curr <run-id>
"""

import argparse
import json
import sys
from pathlib import Path

from engine.execution.runner import ExecutionRunner
from engine.coverage.ledger import CoverageLedgerBuilder
from engine.security.rules import SecurityAnalyzer
from engine.reporting.reporter import generate_markdown_report, generate_html_dashboard
from engine.reporting.history import RunHistoryManager
from validators.validate_inventory import validate_inventory_file
from validators.validate_testspec import validate_testspec_file
from validators.validate_execution import validate_execution_file
from validators.validate_report import validate_ledger_file

def cmd_validate(args):
    target_type = args.artifact_type
    p = Path(args.file)
    if not p.exists():
        print(f"Error: file not found '{p}'", file=sys.stderr)
        sys.exit(1)

    errors = []
    if target_type == "inventory":
        errors = validate_inventory_file(p)
    elif target_type == "testspec":
        errors = validate_testspec_file(p)
    elif target_type == "execution":
        errors = validate_execution_file(p)
    elif target_type == "ledger":
        errors = validate_ledger_file(p)
    else:
        print(f"Unknown artifact type '{target_type}'", file=sys.stderr)
        sys.exit(1)

    if errors:
        print(f"❌ Validation failed for {target_type} ({p}):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print(f"✅ {target_type.capitalize()} validation passed successfully: {p}")

def cmd_execute(args):
    spec_path = Path(args.spec)
    if not spec_path.exists():
        print(f"Error: spec file not found '{spec_path}'", file=sys.stderr)
        sys.exit(1)

    with open(spec_path, "r", encoding="utf-8") as f:
        spec = json.load(f)

    runner = ExecutionRunner(
        base_url=args.base_url,
        timeout=args.timeout,
        allow_destructive=args.allow_destructive,
    )

    out_dir = Path(args.out_dir or "api-audit")
    out_dir.mkdir(parents=True, exist_ok=True)

    run_id = args.run_id or f"run_{spec.get('specification_id', 'audit')}"
    print(f"🚀 Executing test suite against '{args.base_url}' (run_id: {run_id})...")

    results = runner.run_suite(spec, run_id=run_id)

    res_file = out_dir / "execution-results.json"
    with open(res_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    sum_info = results["summary"]
    print(f"✅ Execution finished: {sum_info['passed']}/{sum_info['total']} passed, "
          f"{sum_info['failed']} failed, {sum_info['skipped']} skipped. ({sum_info['pass_rate']}% pass rate)")
    print(f"📄 Saved results to {res_file}")

def cmd_coverage(args):
    inv_path = Path(args.inventory)
    res_path = Path(args.results)

    with open(inv_path, "r", encoding="utf-8") as f:
        inv = json.load(f)
    with open(res_path, "r", encoding="utf-8") as f:
        res = json.load(f)

    run_id = res.get("run_id", "run-001")
    builder = CoverageLedgerBuilder(run_id=run_id)

    # Ingest sources
    for s in inv.get("discovery_sources", []):
        if isinstance(s, dict):
            builder.record_source(
                name=s.get("source_name", "Source"),
                layer=s.get("source_layer", 1),
                status="complete" if s.get("inspected") else "skipped",
                endpoints_yielded=s.get("endpoints_found", 0),
            )

    # Ingest endpoints
    for ep in inv.get("endpoints", []):
        eid = ep.get("endpoint_id")
        builder.record_discovery(
            endpoint_id=eid,
            method=ep.get("method"),
            path=ep.get("path_template"),
            status=ep.get("discovery_status", "confirmed"),
        )
        # Check understanding
        has_auth = "authentication" in ep
        has_params = "parameters" in ep
        builder.record_understanding(
            endpoint_id=eid,
            status="complete" if (has_auth and has_params) else "partial",
            auth_mapped=has_auth,
            params_mapped=has_params,
        )

    # Map execution results
    ep_results = {}
    for r in res.get("results", []):
        eid = r.get("endpoint_id")
        if eid not in ep_results:
            ep_results[eid] = {"executed": 0, "passed": 0, "failed": 0, "skipped": 0, "categories": []}
        ep_results[eid]["executed"] += 1
        if r.get("outcome") == "passed":
            ep_results[eid]["passed"] += 1
        elif r.get("outcome") == "failed":
            ep_results[eid]["failed"] += 1
        elif r.get("outcome") == "skipped":
            ep_results[eid]["skipped"] += 1

    for eid, counts in ep_results.items():
        builder.record_scenarios(eid, counts["executed"] + counts["skipped"], ["functional"])
        builder.record_execution(
            endpoint_id=eid,
            executed=counts["executed"],
            passed=counts["passed"],
            failed=counts["failed"],
            skipped=counts["skipped"],
        )

    ledger_data = builder.build()
    out_dir = Path(args.out_dir or "api-audit")
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "coverage-ledger.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ledger_data, f, indent=2)

    md_path = out_dir / "coverage-ledger.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(builder.to_markdown())

    print(f"✅ Coverage ledger generated: {ledger_data['metrics']['coverage_ratio']*100:.1f}% coverage.")
    print(f"📄 Saved {json_path} and {md_path}")

def cmd_security(args):
    inv_path = Path(args.inventory)
    with open(inv_path, "r", encoding="utf-8") as f:
        inv = json.load(f)

    analyzer = SecurityAnalyzer()
    analyzer.analyze_inventory(inv)

    if args.results:
        res_path = Path(args.results)
        if res_path.exists():
            with open(res_path, "r", encoding="utf-8") as f:
                res = json.load(f)
            analyzer.analyze_execution_results(res)

    out_dir = Path(args.out_dir or "api-audit")
    out_dir.mkdir(parents=True, exist_ok=True)

    findings_json = out_dir / "findings.json"
    with open(findings_json, "w", encoding="utf-8") as f:
        json.dump(analyzer.store.list_all(), f, indent=2)

    findings_md = out_dir / "findings.md"
    with open(findings_md, "w", encoding="utf-8") as f:
        f.write(analyzer.store.to_markdown())

    print(f"✅ Security analysis completed: {len(analyzer.store.findings)} findings.")
    print(f"📄 Saved {findings_json} and {findings_md}")

def cmd_report(args):
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        print(f"Error: run directory '{run_dir}' does not exist", file=sys.stderr)
        sys.exit(1)

    def _read_opt(name):
        p = run_dir / name
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    inventory = _read_opt("endpoint-inventory.json")
    execution = _read_opt("execution-results.json")
    ledger = _read_opt("coverage-ledger.json")
    findings = _read_opt("findings.json")
    trend = _read_opt("trend.json")

    md_content = generate_markdown_report(inventory, execution, ledger, findings, trend)
    html_content = generate_html_dashboard(inventory, execution, ledger, findings, trend)

    with open(run_dir / "report.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    with open(run_dir / "reports.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Audit report & dashboard generated in {run_dir}:")
    print(f"  - {run_dir / 'report.md'}")
    print(f"  - {run_dir / 'reports.html'}")

def cmd_history_compare(args):
    mgr = RunHistoryManager(base_audit_dir=args.runs_dir or "api-audit")
    diff = mgr.compare_runs(args.prev, args.curr)
    if getattr(args, "out_file", None):
        out_p = Path(args.out_file)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(diff, f, indent=2)
        print(f"📄 Saved trend comparison to {out_p}")
    else:
        print(json.dumps(diff, indent=2))

def main():
    parser = argparse.ArgumentParser(description="Universal API Assurance (UAA) CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # validate
    v_p = subparsers.add_parser("validate", help="Validate UAA artifacts against schemas")
    v_p.add_argument("artifact_type", choices=["inventory", "testspec", "execution", "ledger"])
    v_p.add_argument("--file", "-f", required=True, help="Path to JSON file")
    v_p.set_defaults(func=cmd_validate)

    # execute
    e_p = subparsers.add_parser("execute", help="Execute test specifications deterministically")
    e_p.add_argument("--spec", "-s", required=True, help="Path to testspec JSON")
    e_p.add_argument("--base-url", "-u", required=True, help="Target API base URL (non-production)")
    e_p.add_argument("--out-dir", "-o", default="api-audit", help="Output directory")
    e_p.add_argument("--run-id", help="Explicit run ID")
    e_p.add_argument("--timeout", type=float, default=10.0, help="Default timeout in seconds")
    e_p.add_argument("--allow-destructive", action="store_true", help="Permit execution of destructive scenarios")
    e_p.set_defaults(func=cmd_execute)

    # coverage
    c_p = subparsers.add_parser("coverage", help="Calculate measurable coverage ledger")
    c_p.add_argument("--inventory", "-i", required=True, help="Path to endpoint-inventory.json")
    c_p.add_argument("--results", "-r", required=True, help="Path to execution-results.json")
    c_p.add_argument("--out-dir", "-o", default="api-audit", help="Output directory")
    c_p.set_defaults(func=cmd_coverage)

    # security-check
    s_p = subparsers.add_parser("security-check", help="Run automated security rule evaluation")
    s_p.add_argument("--inventory", "-i", required=True, help="Path to endpoint-inventory.json")
    s_p.add_argument("--results", "-r", help="Path to execution-results.json")
    s_p.add_argument("--out-dir", "-o", default="api-audit", help="Output directory")
    s_p.set_defaults(func=cmd_security)

    # report
    r_p = subparsers.add_parser("report", help="Generate report.md and reports.html")
    r_p.add_argument("--run-dir", "-d", required=True, help="Directory containing run artifacts")
    r_p.set_defaults(func=cmd_report)

    # history-compare
    h_p = subparsers.add_parser("history-compare", help="Compare two historical runs for regressions")
    h_p.add_argument("--runs-dir", default="api-audit", help="Base directory containing runs/")
    h_p.add_argument("--prev", required=True, help="Previous run ID (e.g. run-001)")
    h_p.add_argument("--curr", required=True, help="Current run ID (e.g. run-002)")
    h_p.add_argument("--out-file", help="Optional path to output comparison JSON")
    h_p.set_defaults(func=cmd_history_compare)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

