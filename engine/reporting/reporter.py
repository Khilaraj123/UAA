"""Report generation engine for Universal API Assurance (UAA).

Generates comprehensive Markdown reports and interactive HTML audit dashboards
with all 6 core sections:
1. Overview
2. Endpoint Explorer
3. Test Explorer
4. Security Findings
5. Failure Analysis
6. Trends & Regression
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import html
import json

def generate_markdown_report(
    inventory: Optional[Dict[str, Any]],
    execution: Optional[Dict[str, Any]],
    ledger: Optional[Dict[str, Any]],
    findings: Optional[List[Dict[str, Any]]],
    trend: Optional[Dict[str, Any]],
) -> str:
    """Generate comprehensive report.md."""
    run_id = execution.get("run_id", "baseline") if execution else "N/A"
    target = execution.get("target_origin", "N/A") if execution else "N/A"
    summary = execution.get("summary", {}) if execution else {}

    lines = [
        f"# Universal API Assurance (UAA) - Audit Report",
        "",
        f"- **Run ID**: `{run_id}`",
        f"- **Target Origin**: `{target}`",
        f"- **Pass Rate**: `{summary.get('pass_rate', 0.0)}%`",
        f"- **Total Scenarios**: `{summary.get('total', 0)}`",
        f"- **Passed**: `{summary.get('passed', 0)}` | **Failed**: `{summary.get('failed', 0)}` | **Skipped**: `{summary.get('skipped', 0)}` | **Errors**: `{summary.get('errors', 0)}`",
        "",
        "---",
        "",
        "## 1. Measurable Coverage Ledger Overview",
        "",
    ]

    if ledger and "metrics" in ledger:
        m = ledger["metrics"]
        lines.extend([
            f"- **Discovered Endpoints**: {m.get('total_endpoints_discovered', 0)}",
            f"- **Understood Endpoints**: {m.get('endpoints_understood', 0)}",
            f"- **Endpoints with Scenarios**: {m.get('endpoints_with_scenarios', 0)}",
            f"- **Endpoints Executed**: {m.get('endpoints_executed', 0)}",
            f"- **Endpoints Verified (Passing)**: {m.get('endpoints_verified_pass', 0)}",
            f"- **Coverage Ratio**: `{m.get('coverage_ratio', 0.0) * 100:.1f}%`",
            f"- **Unverified Remaining**: {m.get('endpoints_unverified', 0)}",
            "",
        ])
    else:
        lines.append("Coverage ledger not loaded or available.\n")

    lines.extend([
        "## 2. Security Audit Findings",
        "",
    ])

    if findings:
        lines.extend([
            f"Identified {len(findings)} security findings:",
            "",
            "| ID | Severity | Category | Endpoint | Title | Status |",
            "|---|---|---|---|---|---|",
        ])
        for f in findings:
            lines.append(f"| `{f.get('finding_id')}` | **{f.get('severity', '').upper()}** | `{f.get('category')}` | `{f.get('endpoint_id')}` | {f.get('title')} | `{f.get('status')}` |")
        lines.append("")
    else:
        lines.append("No security vulnerabilities or flaws identified in this run.\n")

    lines.extend([
        "## 3. Failure Analysis & Root-Cause Hypotheses",
        "",
    ])

    failed_scenarios = [r for r in (execution.get("results", []) if execution else []) if r.get("outcome") in ("failed", "error")]
    if failed_scenarios:
        for fs in failed_scenarios:
            scen_id = fs.get("scenario_id")
            ep_id = fs.get("endpoint_id")
            err_msg = fs.get("error_message")
            lines.extend([
                f"### ❌ Scenario `{scen_id}` ({ep_id})",
                f"- **Outcome**: `{fs.get('outcome')}`",
                f"- **HTTP Status**: `{fs.get('http_status')}`",
            ])
            if err_msg:
                lines.append(f"- **Error**: {err_msg}")
            
            failed_assertions = [a for a in fs.get("assertions", []) if not a.get("passed")]
            if failed_assertions:
                lines.append("- **Failed Assertions**:")
                for fa in failed_assertions:
                    lines.append(f"  - `{fa.get('type')}` ({fa.get('path') or fa.get('name')}): expected `{fa.get('expected')}`, got `{fa.get('actual')}` — {fa.get('message')}")
            lines.append("")
    else:
        lines.append("All executed scenarios passed successfully.\n")

    lines.extend([
        "## 4. Historical Trends & Regressions",
        "",
    ])
    if trend and trend.get("status") == "compared":
        lines.extend([
            f"- **Compared Against**: `{trend.get('previous_run_id')}`",
            f"- **Pass Rate Delta**: `{trend.get('pass_rate_delta'):+0.2f}%` ({trend.get('pass_rate_previous')}% -> {trend.get('pass_rate_current')}%)",
            f"- **Regressions Detected**: `{trend.get('regression_count')}`",
            f"- **Fixes Verified**: `{trend.get('fix_count')}`",
        ])
        if trend.get("missing_scenario_count"):
            lines.append(f"- **Missing Scenarios (Coverage Loss)**: `{trend.get('missing_scenario_count')}`")
        if trend.get("new_scenario_count"):
            lines.append(f"- **New Scenarios**: `{trend.get('new_scenario_count')}`")
        lines.append("")
        if trend.get("regressions"):
            lines.append("### 🚨 Regressions")
            for reg in trend["regressions"]:
                lines.append(f"- {reg.get('message')}")
            lines.append("")
        if trend.get("missing_scenarios"):
            lines.append("### ⚠️ Missing Scenarios (Coverage Loss)")
            for ms in trend["missing_scenarios"]:
                lines.append(f"- {ms.get('message')}")
            lines.append("")
        if trend.get("new_scenarios"):
            lines.append("### 🆕 New Scenarios")
            for ns in trend["new_scenarios"]:
                lines.append(f"- {ns.get('message')}")
            lines.append("")
    else:
        lines.append("Trend unavailable — baseline run.\n")

    return "\n".join(lines)


def generate_html_dashboard(
    inventory: Optional[Dict[str, Any]],
    execution: Optional[Dict[str, Any]],
    ledger: Optional[Dict[str, Any]],
    findings: Optional[List[Dict[str, Any]]],
    trend: Optional[Dict[str, Any]],
) -> str:
    """Generate standalone interactive HTML audit dashboard."""
    run_id = html.escape(execution.get("run_id", "run-baseline") if execution else "N/A")
    target = html.escape(execution.get("target_origin", "N/A") if execution else "N/A")
    summary = execution.get("summary", {}) if execution else {}
    results = execution.get("results", []) if execution else []
    endpoints = inventory.get("endpoints", []) if inventory else []
    metrics = ledger.get("metrics", {}) if ledger else {}
    findings_list = findings or []

    # Encode raw data safely as JSON for the client-side interactive viewer
    data_bundle = {
        "run_id": run_id,
        "target": target,
        "summary": summary,
        "metrics": metrics,
        "endpoints": endpoints,
        "results": results,
        "findings": findings_list,
        "trend": trend or {},
    }
    json_blob = json.dumps(data_bundle).replace("</script>", "<\\/script>")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>UAA Audit Dashboard - {run_id}</title>
  <style>
    :root {{
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-muted: #8b949e;
      --text-bright: #f0f6fc;
      --pass: #238636;
      --fail: #da3633;
      --warn: #d29922;
      --info: #58a6ff;
      --font-mono: 'Consolas', 'Courier New', monospace;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
      padding: 24px;
    }}
    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 24px;
    }}
    h1 {{ font-size: 24px; color: var(--text-bright); }}
    .badge {{
      display: inline-block;
      padding: 3px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
    }}
    .badge-pass {{ background: var(--pass); color: #fff; }}
    .badge-fail {{ background: var(--fail); color: #fff; }}
    .badge-warn {{ background: var(--warn); color: #fff; }}
    .badge-info {{ background: var(--info); color: #fff; }}
    nav {{
      display: flex;
      gap: 12px;
      margin-bottom: 24px;
      border-bottom: 1px solid var(--border);
    }}
    nav button {{
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 10px 16px;
      cursor: pointer;
      font-size: 14px;
      font-weight: 600;
      border-bottom: 2px solid transparent;
    }}
    nav button.active {{
      color: var(--info);
      border-bottom-color: var(--info);
    }}
    .tab-content {{ display: none; }}
    .tab-content.active {{ display: block; }}
    .grid-cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card {{
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 16px;
    }}
    .card-title {{ font-size: 13px; color: var(--text-muted); margin-bottom: 8px; text-transform: uppercase; }}
    .card-value {{ font-size: 28px; font-weight: bold; color: var(--text-bright); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 16px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }}
    th, td {{
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      font-size: 14px;
    }}
    th {{ background: #21262d; color: var(--text-bright); }}
    code {{
      font-family: var(--font-mono);
      background: rgba(110,118,129,0.2);
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 13px;
    }}
    .search-input {{
      width: 100%;
      max-width: 400px;
      padding: 8px 12px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      color: var(--text-bright);
      margin-bottom: 16px;
    }}
    pre {{
      background: #090d13;
      padding: 12px;
      border-radius: 6px;
      overflow-x: auto;
      font-family: var(--font-mono);
      font-size: 13px;
      border: 1px solid var(--border);
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Universal API Assurance (UAA) Dashboard</h1>
      <p style="color: var(--text-muted); font-size: 14px;">Run ID: <code>{run_id}</code> | Target: <code>{target}</code></p>
    </div>
    <span class="badge badge-info">v2.0.0</span>
  </header>

  <nav id="nav-tabs">
    <button class="active" onclick="showTab('overview')">1. Overview</button>
    <button onclick="showTab('endpoints')">2. Endpoint Explorer</button>
    <button onclick="showTab('tests')">3. Test Explorer</button>
    <button onclick="showTab('security')">4. Security Findings</button>
    <button onclick="showTab('failures')">5. Failure Analysis</button>
    <button onclick="showTab('trends')">6. Trends & Regression</button>
  </nav>

  <!-- TAB 1: OVERVIEW -->
  <section id="tab-overview" class="tab-content active">
    <div class="grid-cards">
      <div class="card">
        <div class="card-title">Pass Rate</div>
        <div class="card-value" style="color: var(--info);">{summary.get('pass_rate', 0.0)}%</div>
      </div>
      <div class="card">
        <div class="card-title">Discovered Endpoints</div>
        <div class="card-value">{metrics.get('total_endpoints_discovered', len(endpoints))}</div>
      </div>
      <div class="card">
        <div class="card-title">Coverage Ratio</div>
        <div class="card-value">{round(metrics.get('coverage_ratio', 0.0) * 100, 1)}%</div>
      </div>
      <div class="card">
        <div class="card-title">Security Findings</div>
        <div class="card-value" style="color: {('var(--fail)' if findings_list else 'var(--pass)')};">{len(findings_list)}</div>
      </div>
    </div>

    <div class="card">
      <h3 style="color: var(--text-bright); margin-bottom: 12px;">Execution Breakdown</h3>
      <p>Total Scenarios: <strong>{summary.get('total', 0)}</strong> | Passed: <strong style="color:var(--pass);">{summary.get('passed', 0)}</strong> | Failed: <strong style="color:var(--fail);">{summary.get('failed', 0)}</strong> | Skipped: <strong style="color:var(--warn);">{summary.get('skipped', 0)}</strong> | Errors: <strong>{summary.get('errors', 0)}</strong></p>
    </div>
  </section>

  <!-- TAB 2: ENDPOINT EXPLORER -->
  <section id="tab-endpoints" class="tab-content">
    <input type="text" id="endpoint-search" class="search-input" placeholder="Search path, method, or tag..." onkeyup="filterEndpoints()">
    <table id="endpoint-table">
      <thead>
        <tr>
          <th>Method</th>
          <th>Path Template</th>
          <th>Discovery Status</th>
          <th>Confidence</th>
          <th>Auth Required</th>
          <th>Side Effect Risk</th>
        </tr>
      </thead>
      <tbody id="endpoint-tbody">
      </tbody>
    </table>
  </section>

  <!-- TAB 3: TEST EXPLORER -->
  <section id="tab-tests" class="tab-content">
    <input type="text" id="test-search" class="search-input" placeholder="Search scenario ID, endpoint, or category..." onkeyup="filterTests()">
    <table id="test-table">
      <thead>
        <tr>
          <th>Scenario ID</th>
          <th>Endpoint</th>
          <th>Outcome</th>
          <th>HTTP Status</th>
          <th>Duration</th>
          <th>Assertions</th>
        </tr>
      </thead>
      <tbody id="test-tbody">
      </tbody>
    </table>
  </section>

  <!-- TAB 4: SECURITY FINDINGS -->
  <section id="tab-security" class="tab-content">
    <div id="security-container"></div>
  </section>

  <!-- TAB 5: FAILURE ANALYSIS -->
  <section id="tab-failures" class="tab-content">
    <div id="failures-container"></div>
  </section>

  <!-- TAB 6: TRENDS & REGRESSION -->
  <section id="tab-trends" class="tab-content">
    <div id="trends-container"></div>
  </section>

  <script>
    const data = {json_blob};

    function showTab(tabId) {{
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('#nav-tabs button').forEach(el => el.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
      event.target.classList.add('active');
    }}

    function renderEndpoints() {{
      const tbody = document.getElementById('endpoint-tbody');
      tbody.innerHTML = '';
      data.endpoints.forEach(ep => {{
        const tr = document.createElement('tr');
        const authReq = ep.authentication && ep.authentication.required ? '🔒 Yes' : '🔓 Public';
        tr.innerHTML = `
          <td><strong>${{ep.method}}</strong></td>
          <td><code>${{ep.path_template}}</code></td>
          <td><span class="badge badge-info">${{ep.discovery_status}}</span></td>
          <td>${{ep.confidence}}</td>
          <td>${{authReq}}</td>
          <td><code>${{ep.side_effect_risk}}</code></td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function renderTests() {{
      const tbody = document.getElementById('test-tbody');
      tbody.innerHTML = '';
      data.results.forEach(res => {{
        const tr = document.createElement('tr');
        const badgeClass = res.outcome === 'passed' ? 'badge-pass' : (res.outcome === 'failed' ? 'badge-fail' : 'badge-warn');
        const passedAss = (res.assertions || []).filter(a => a.passed).length;
        const totalAss = (res.assertions || []).length;
        tr.innerHTML = `
          <td><code>${{res.scenario_id}}</code></td>
          <td><code>${{res.endpoint_id}}</code></td>
          <td><span class="badge ${{badgeClass}}">${{res.outcome}}</span></td>
          <td>${{res.http_status || '-'}}</td>
          <td>${{res.duration_ms ? res.duration_ms + 'ms' : '-'}}</td>
          <td>${{passedAss}} / ${{totalAss}} passed</td>
        `;
        tbody.appendChild(tr);
      }});
    }}

    function renderSecurity() {{
      const container = document.getElementById('security-container');
      if (!data.findings || data.findings.length === 0) {{
        container.innerHTML = '<div class="card"><p style="color:var(--pass);">✅ No security findings identified.</p></div>';
        return;
      }}
      container.innerHTML = data.findings.map(f => `
        <div class="card" style="margin-bottom:16px;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
            <h3 style="color:var(--text-bright); font-size:16px;">${{f.title}} (<code>${{f.finding_id}}</code>)</h3>
            <span class="badge badge-fail">${{f.severity.toUpperCase()}}</span>
          </div>
          <p><strong>Endpoint:</strong> <code>${{f.endpoint_id}}</code> | <strong>Category:</strong> <code>${{f.category}}</code></p>
          <p style="margin: 8px 0;">${{f.description}}</p>
          <p><strong>Impact:</strong> ${{f.impact}}</p>
          <div style="margin-top:8px;">
            <strong>Remediation:</strong>
            <p>${{f.remediation.guidance}}</p>
          </div>
        </div>
      `).join('');
    }}

    function renderFailures() {{
      const container = document.getElementById('failures-container');
      const failed = data.results.filter(r => r.outcome === 'failed' || r.outcome === 'error');
      if (failed.length === 0) {{
        container.innerHTML = '<div class="card"><p style="color:var(--pass);">✅ No scenario failures observed in this run.</p></div>';
        return;
      }}
      container.innerHTML = failed.map(f => `
        <div class="card" style="margin-bottom:16px;">
          <h3 style="color:var(--fail); font-size:16px;">❌ Scenario ${{f.scenario_id}} (<code>${{f.endpoint_id}}</code>)</h3>
          <p>Outcome: <strong>${{f.outcome}}</strong> | HTTP Status: <strong>${{f.http_status || 'N/A'}}</strong></p>
          ${{f.error_message ? `<p style="color:var(--fail);">${{f.error_message}}</p>` : ''}}
          <div style="margin-top:12px;">
            <strong>Failed Assertions:</strong>
            ${{(f.assertions || []).filter(a => !a.passed).map(a => `
              <div style="background:#21262d; padding:8px; border-radius:4px; margin-top:6px;">
                <code>${{a.type}}</code>: ${{a.message}}
              </div>
            `).join('')}}
          </div>
        </div>
      `).join('');
    }}

    function renderTrends() {{
      const container = document.getElementById('trends-container');
      const tr = data.trend;
      if (!tr || tr.status !== 'compared') {{
        container.innerHTML = '<div class="card"><p style="color:var(--text-muted);">Baseline run. Historical regression trend available after subsequent runs.</p></div>';
        return;
      }}
      const missingHtml = tr.missing_scenarios && tr.missing_scenarios.length ? `
        <div style="margin-top:16px;">
          <h4 style="color:var(--fail); font-size:14px; margin-bottom:8px;">⚠️ Missing Scenarios (Coverage Loss) (${{tr.missing_scenario_count}})</h4>
          ${{tr.missing_scenarios.map(m => `
            <div style="background:#21262d; padding:8px; border-radius:4px; margin-top:6px;">
              <code>${{m.scenario_id}}</code>: ${{m.message}}
            </div>
          `).join('')}}
        </div>
      ` : '';
      const newHtml = tr.new_scenarios && tr.new_scenarios.length ? `
        <div style="margin-top:16px;">
          <h4 style="color:var(--info, #58a6ff); font-size:14px; margin-bottom:8px;">🆕 New Scenarios (${{tr.new_scenario_count}})</h4>
          ${{tr.new_scenarios.map(n => `
            <div style="background:#21262d; padding:8px; border-radius:4px; margin-top:6px;">
              <code>${{n.scenario_id}}</code>: ${{n.message}}
            </div>
          `).join('')}}
        </div>
      ` : '';
      const regressionsHtml = tr.regressions && tr.regressions.length ? `
        <div style="margin-top:16px;">
          <h4 style="color:var(--fail); font-size:14px; margin-bottom:8px;">🚨 Regressions (${{tr.regression_count}})</h4>
          ${{tr.regressions.map(r => `
            <div style="background:#21262d; padding:8px; border-radius:4px; margin-top:6px;">
              <code>${{r.scenario_id}}</code>: ${{r.message}}
            </div>
          `).join('')}}
        </div>
      ` : '';
      container.innerHTML = `
        <div class="card">
          <h3 style="color:var(--text-bright); margin-bottom:12px;">Historical Run Comparison</h3>
          <p>Compared: <code>${{tr.previous_run_id}}</code> &rarr; <code>${{tr.current_run_id}}</code></p>
          <p>Pass Rate Delta: <strong>${{tr.pass_rate_delta >= 0 ? '+' : ''}}${{tr.pass_rate_delta}}%</strong> (${{tr.pass_rate_previous}}% &rarr; ${{tr.pass_rate_current}}%)</p>
          <p>Regressions: <strong style="color:var(--fail);">${{tr.regression_count}}</strong> | Fixes: <strong style="color:var(--pass);">${{tr.fix_count}}</strong></p>
          ${{tr.missing_scenario_count ? `<p>Missing Scenarios (Coverage Loss): <strong style="color:var(--fail);">${{tr.missing_scenario_count}}</strong></p>` : ''}}
          ${{tr.new_scenario_count ? `<p>New Scenarios: <strong>${{tr.new_scenario_count}}</strong></p>` : ''}}
          ${{regressionsHtml}}
          ${{missingHtml}}
          ${{newHtml}}
        </div>
      `;
    }}

    function filterEndpoints() {{
      const q = document.getElementById('endpoint-search').value.toLowerCase();
      document.querySelectorAll('#endpoint-tbody tr').forEach(row => {{
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}

    function filterTests() {{
      const q = document.getElementById('test-search').value.toLowerCase();
      document.querySelectorAll('#test-tbody tr').forEach(row => {{
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}

    // Initial renders
    renderEndpoints();
    renderTests();
    renderSecurity();
    renderFailures();
    renderTrends();
  </script>
</body>
</html>
"""

