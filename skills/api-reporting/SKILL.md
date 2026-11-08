---
name: api-reporting
description: Generate comprehensive Markdown audit reports, measurable coverage ledgers, and interactive HTML dashboards with historical regression comparison.
---

# API Reporting Skill

## Mission
Synthesize discovery inventories, execution results, measurable coverage ledgers, and security findings into an actionable audit dashboard. Compare current run against prior historical runs to detect regressions and newly exposed or fixed endpoints.

## Core Deliverables
1. **Measurable Coverage Ledger (`coverage-ledger.json` & `coverage-ledger.md`)**:
   - Explicitly records verified endpoints vs. unverified surfaces.
   - For every unverified endpoint, documents the exact blocking reason (destructive action, missing credentials, dynamic mock required).
2. **Comprehensive Markdown Report (`report.md`)**:
   - Executive summary, pass/fail statistics, security findings with severity badges, failed assertion breakdowns, and regression notes.
3. **Interactive Audit Dashboard (`reports.html`)**:
   - Single-file standalone HTML application featuring all 6 core tabs:
     1. **Overview**: Key metrics cards, pass rates, coverage ratio, execution breakdown.
     2. **Endpoint Explorer**: Interactive search and filtering by HTTP method, path, and safety risk.
     3. **Test Explorer**: Scenario browser with requests, responses, and assertion results.
     4. **Security Findings**: OWASP vulnerability findings with severity badges, evidence, and remediation diffs.
     5. **Failure Analysis**: Failed assertions, expected vs. actual values, and root-cause hypotheses.
     6. **Trends & Regression**: Historical comparison against prior runs, regression alerts, and verified fixes.

## Historical Integrity Rules
- Never overwrite previous audit runs. Every run is stored in `api-audit/runs/run-XXX/`.
- If no previous run exists, state clearly: `Trend unavailable — baseline run`.
- Never claim 100% coverage automatically without ledger justification.

