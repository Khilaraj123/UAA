---
name: api-test-execution
description: Execute approved test scenarios deterministically using the zero-dependency Python execution runner against approved non-production targets.
---

# API Test Execution Skill

## Mission
Execute approved test scenarios deterministically. Never make AI-based pass/fail decisions: pass/fail is determined strictly by the deterministic assertion evaluator. Enforce non-production target restrictions and redact sensitive data.

## Execution Rules
1. **Target Verification**:
   - The `--base-url` MUST be explicitly approved by the user. Never infer a production URL from source code or comments.
   - If no base URL is provided, STOP and request approval from the user.
2. **Environment & Secrets**:
   - Resolve `${ENV_VAR}` variables from the host environment.
   - Fail closed: If an environment variable is missing, abort the scenario with an explicit error.
   - Redact all sensitive tokens, cookies, and passwords from request/response logs.
3. **Deterministic Execution**:
   - Scenarios execute sequentially in lexical order of `scenario_id`.
   - Suppress redirects (no automatic redirect following) to assert on redirect status codes (301, 302, 307, 308).
   - Timeouts are strictly bounded (default 10s, max 60s).
   - Truncate response bodies exceeding 2MB to protect against denial-of-service/memory exhaustion.
4. **Execution Command**:
   ```bash
   python -m engine.cli execute \
     --spec api-audit/testspecifications.json \
     --base-url http://127.0.0.1:8000 \
     --out-dir api-audit/runs/run-001/
   ```

## Output Contract
Generates `execution-results.json` adhering to `schemas/execution.schema.json`.
Each result contains:
- `scenario_id` & `endpoint_id`
- `outcome`: `passed`, `failed`, `skipped`, or `error`
- Exact HTTP status and elapsed duration in milliseconds
- Redacted request and response payloads
- Array of evaluated assertions with expected vs. actual values

