#!/usr/bin/env python3
"""Deterministic standard-library HTTP test runner for API Audit and Test."""
import argparse, datetime as dt, html, json, os, re, ssl, sys, time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlencode
from urllib.request import Request, build_opener, HTTPSHandler, HTTPHandler, ProxyHandler, HTTPRedirectHandler

VERSION = "1.0.0"
MAX_BODY = 2_000_000
SECRET_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key", "proxy-authorization"}
ENV = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def expand(value):
    if isinstance(value, str):
        def sub(m):
            key = m.group(1)
            if key not in os.environ:
                raise ValueError("Missing required environment variable: " + key)
            return os.environ[key]
        return ENV.sub(sub, value)
    if isinstance(value, list): return [expand(x) for x in value]
    if isinstance(value, dict): return {k: expand(v) for k, v in value.items()}
    return value

def redact_headers(headers):
    return {k: ("[REDACTED]" if k.lower() in SECRET_HEADERS else v) for k, v in headers.items()}

def redact_json(value, extra=()):
    hidden = {"password", "token", "access_token", "refresh_token", "secret", "api_key"} | {x.lower() for x in extra}
    if isinstance(value, dict): return {k: ("[REDACTED]" if k.lower() in hidden else redact_json(v, extra)) for k, v in value.items()}
    if isinstance(value, list): return [redact_json(x, extra) for x in value]
    return value

def get_path(value, path):
    if path in ("", "$", None): return value
    for part in path.removeprefix("$.").split("."):
        if isinstance(value, list) and part.isdigit(): value = value[int(part)]
        elif isinstance(value, dict): value = value[part]
        else: raise KeyError(part)
    return value

def assertion_result(a, status, headers, body_text, body_json):
    kind, expected, path = a["type"], a.get("expected"), a.get("path", "")
    actual, ok = None, False
    if kind == "status": actual, ok = status, status == expected
    elif kind in ("header_equals", "header_exists", "content_type"):
        actual = next((v for k, v in headers.items() if k.lower() == (a.get("name", "content-type") if kind != "content_type" else "content-type").lower()), None)
        ok = actual is not None and (kind == "header_exists" or (expected.lower() in actual.lower() if kind == "content_type" else actual == expected))
    elif kind in ("json_equals", "json_exists", "json_type"):
        try:
            actual = get_path(body_json, path)
            if kind == "json_equals": ok = actual == expected
            elif kind == "json_exists": ok = True
            else:
                typ = "null" if actual is None else "boolean" if isinstance(actual, bool) else "object" if isinstance(actual, dict) else "array" if isinstance(actual, list) else "number" if isinstance(actual, (int, float)) else "string"
                ok = typ == expected
        except (KeyError, IndexError, TypeError, ValueError): pass
    elif kind == "text_contains": actual, ok = body_text[:MAX_BODY], str(expected) in body_text
    elif kind == "text_not_contains": actual, ok = body_text[:MAX_BODY], str(expected) not in body_text
    else: raise ValueError("Unsupported assertion: " + kind)
    return {"type": kind, "path": path or None, "expected": expected, "actual": actual, "passed": bool(ok)}

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def perform(base, scenario, timeout, redact_keys):
    r = expand(scenario.get("request", {})); method = r.get("method", "GET").upper(); path = r.get("path", "/")
    url = base.rstrip("/") + (path if path.startswith("/") else "/" + path)
    if r.get("query"):
        url += ("&" if "?" in url else "?") + urlencode(r["query"], doseq=True)
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname: raise ValueError("Only HTTP(S) URLs are supported")
    headers = dict(r.get("headers", {})); body = r.get("body"); data = None
    if body is not None:
        data = body.encode() if isinstance(body, str) else json.dumps(body).encode()
        if not any(k.lower() == "content-type" for k in headers): headers["Content-Type"] = "application/json"
    req = Request(url, data=data, headers=headers, method=method)
    opener = build_opener(ProxyHandler(), NoRedirect(), HTTPSHandler(context=ssl.create_default_context()), HTTPHandler())
    start = time.monotonic()
    try:
        response = opener.open(req, timeout=min(float(r.get("timeout_seconds", timeout)), 60))
        status, response_headers, raw = response.status, dict(response.headers.items()), response.read(MAX_BODY + 1)
    except HTTPError as e:
        status, response_headers, raw = e.code, dict(e.headers.items()), e.read(MAX_BODY + 1)
    duration = round((time.monotonic() - start) * 1000, 2); truncated = len(raw) > MAX_BODY
    text_body = raw[:MAX_BODY].decode("utf-8", errors="replace")
    try: parsed_body = json.loads(text_body) if text_body else None
    except json.JSONDecodeError: parsed_body = None
    checks = [assertion_result(a, status, response_headers, text_body, parsed_body) for a in scenario.get("assertions", [])]
    return {"status": status, "duration_ms": duration, "headers": redact_headers(response_headers),
            "body": redact_json(parsed_body, redact_keys) if parsed_body is not None else text_body[:4000],
            "body_truncated": truncated, "assertions": checks, "passed": all(x["passed"] for x in checks),
            "request": {"method": method, "path": path, "headers": redact_headers(headers)}}

def make_md(result):
    s = result["summary"]
    out = ["# API Execution Results", "", f"- Run: `{result['run_id']}`", f"- Target: `{result['target_origin']}`",
           f"- Passed: {s['passed']} | Failed: {s['failed']} | Skipped: {s['skipped']} | Errors: {s['errors']}",
           f"- Pass rate: {s['pass_rate']}% of executed scenarios", "", "## Scenarios", "",
           "| Scenario | Endpoint | HTTP | Duration | Result |", "|---|---|---:|---:|---|"]
    for x in result["scenarios"]: out.append(f"| {x['scenario_id']} | {x.get('endpoint_id','')} | {x.get('http_status','—')} | {x.get('duration_ms','—')} ms | {x['status']} |")
    out += ["", "## Failures and errors", ""]
    bad = [x for x in result["scenarios"] if x["status"] in ("failed", "error")]
    if not bad: out.append("No failures or errors.")
    for x in bad:
        out += [f"### {x['scenario_id']} — {x['status']}", "", f"- Endpoint: `{x.get('endpoint_id','')}`", f"- Error: {x.get('error','')}", ""]
        for a in x.get("assertions", []):
            if not a["passed"]: out.append(f"- `{a['type']}` expected `{a.get('expected')}`, actual `{a.get('actual')}`")
    return "\n".join(out)

def make_html(result):
    s = result["summary"]; rows = []
    for x in result["scenarios"]:
        rows.append("<tr><td>"+html.escape(x["scenario_id"])+"</td><td>"+html.escape(x.get("endpoint_id", ""))+"</td><td>"+html.escape(str(x.get("http_status", "—")))+"</td><td>"+html.escape(str(x.get("duration_ms", "—")))+" ms</td><td><b class='"+x["status"]+"'>"+x["status"]+"</b></td></tr>")
    cards = "".join(f"<article><small>{k}</small><strong>{s[k]}</strong></article>" for k in ("passed", "failed", "skipped", "errors"))
    return """<!doctype html><html lang='en'><meta charset='utf-8'><meta name='viewport' content='width=device-width'><title>API Audit Dashboard</title><style>
body{font:15px system-ui;margin:32px auto;padding:0 18px;max-width:1100px;background:#f5f7fb;color:#182230}h1{margin-bottom:4px}.muted,small{color:#667085}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:22px 0}article,section{background:white;border:1px solid #e5e9f0;border-radius:12px;padding:16px}strong{display:block;font-size:28px}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:12px;border-bottom:1px solid #e5e9f0}.passed{color:#067647}.failed,.error{color:#b42318}.skipped{color:#667085}</style><h1>API Audit Dashboard</h1>
<p class='muted'>"""+html.escape(result["run_id"])+" · "+html.escape(result["target_origin"])+" · Pass rate "+str(s["pass_rate"])+"%</p><div class='cards'>"+cards+"</div><section><h2>Scenario results</h2><table><thead><tr><th>Scenario</th><th>Endpoint</th><th>HTTP</th><th>Duration</th><th>Result</th></tr></thead><tbody>"+"".join(rows)+"</tbody></table></section><section style='margin-top:16px'><h2>Trend</h2><p class='muted'>Trend unavailable — baseline run. Compare a compatible previous run to calculate trends.</p></section></html>"

def main():
    p = argparse.ArgumentParser(description=__doc__); sub = p.add_subparsers(dest="command", required=True)
    e = sub.add_parser("execute"); e.add_argument("--spec", required=True); e.add_argument("--base-url", required=True); e.add_argument("--out", default="api-audit/execution-results.json"); e.add_argument("--timeout", type=float, default=10)
    a = p.parse_args()
    if a.timeout <= 0: p.error("--timeout must be positive")
    base = a.base_url.rstrip("/"); u = urlsplit(base)
    if u.scheme not in ("http", "https") or not u.hostname: p.error("--base-url must be an absolute HTTP(S) URL")
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8")); scenarios = sorted(spec.get("scenarios", []), key=lambda x: x["scenario_id"])
    counts = {k: 0 for k in ("passed", "failed", "skipped", "errors")}; records = []
    for scenario in scenarios:
        rec = {"scenario_id": scenario["scenario_id"], "endpoint_id": scenario.get("endpoint_id"), "title": scenario.get("title", "")}
        if not scenario.get("enabled", True) or scenario.get("needs_review") or scenario.get("safety", "unknown") != "read_only":
            rec.update(status="skipped", skip_reason=scenario.get("skip_reason", "Disabled, review-required, or non-read-only; starter runner is read-only by default")); counts["skipped"] += 1
        else:
            try:
                r = perform(base, scenario, a.timeout, spec.get("redact_json_keys", [])); state = "passed" if r["passed"] else "failed"
                rec.update(status=state, http_status=r["status"], duration_ms=r["duration_ms"], assertions=r["assertions"], response_headers=r["headers"], response_body=r["body"], body_truncated=r["body_truncated"], request=r["request"]); counts[state] += 1
            except Exception as ex:
                rec.update(status="error", error=f"{type(ex).__name__}: {ex}"); counts["errors"] += 1
        records.append(rec)
    executed = counts["passed"] + counts["failed"] + counts["errors"]
    summary = {**counts, "total": len(records), "executed": executed, "pass_rate": round(counts["passed"] / executed * 100, 2) if executed else 0.0}
    now = dt.datetime.now(dt.timezone.utc).isoformat(); origin = f"{u.scheme}://{u.netloc}"
    result = {"schema_version": "1.0", "runner_version": VERSION, "run_id": dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"), "executed_at": now, "target_origin": origin, "summary": summary, "scenarios": records}
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True); out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    (out.parent / "execution-results.md").write_text(make_md(result), encoding="utf-8")
    (out.parent / "reports.html").write_text(make_html(result), encoding="utf-8")
    report = ["# API Audit Report", "", f"- Executed: `{now}`", f"- Target: `{origin}`", f"- Runner: `{VERSION}`", f"- Scenarios: {summary['total']}", f"- Passed / failed / skipped / errors: {counts['passed']} / {counts['failed']} / {counts['skipped']} / {counts['errors']}", f"- Pass rate: {summary['pass_rate']}% of executed scenarios", "- Trend: unavailable — baseline run.", "", "## Limitations", "", "HTTP assertions do not prove complete security, business correctness, load capacity, or production readiness.", "", "## Scenario details", ""]
    report += [f"- **{x['scenario_id']}** — {x['status']}" + (f": {x['error']}" if x.get("error") else "") for x in records]
    (out.parent / "report.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps(summary, indent=2)); return 1 if counts["failed"] or counts["errors"] else 0

if __name__ == "__main__": sys.exit(main())
