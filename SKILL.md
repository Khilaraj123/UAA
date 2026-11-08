---
name: uaa
description: Universal API Assurance (UAA) — Autonomous, framework-agnostic API discovery, understanding, security auditing, deterministic testing, and evidence-backed reporting. Activated by the /uaa slash command or whenever asked to audit, discover, test, or verify APIs.
metadata:
  icon: verified_user
---

# Universal API Assurance (UAA)

Autonomous, framework-agnostic, and protocol-independent API assurance ecosystem. Unifies 6-layer source discovery, semantic code understanding, deterministic testing, automated OWASP security auditing, and continuous multi-run regression tracking.

## Slash Command Usage (`/uaa`)

When the user triggers `/uaa` in the chat input:

```text
/uaa                                 # Interactive audit of current workspace
/uaa discover                        # Discover endpoints & reconcile contracts (read-only)
/uaa plan                            # Discover, trace, and synthesize test specifications
/uaa execute --base-url <url>        # Execute existing test specifications against non-prod target
/uaa security                        # Run OWASP API Top 10 security audit
/uaa report                          # Rebuild reports.html dashboard and report.md
/uaa full --base-url <url>           # Complete lifecycle with approval gates
```

If no arguments are provided with `/uaa`, default to **interactive audit mode**: inspect the workspace, discover endpoints, trace contracts, present the findings and test plan, and request approval of a non-production `--base-url` before executing tests.

---

## Safety and Truthfulness Rules

- **Strict Non-Production Execution**: NEVER execute requests against production. Require explicit confirmation of a non-production `--base-url` (e.g. `http://127.0.0.1:8000`, `http://localhost:5000`).
- **Read-Only Discovery by Default**: Discovery and planning must never mutate application code, databases, or infrastructure.
- **Destructive Mutation Protection**: Operations marked `destructive` (DELETE, drop, reset) or `external_effect` (payments, emails, SMS) are disabled by default. Require explicit operator approval.
- **Deterministic Evaluation**: AI designs scenarios; only the zero-dependency Python runner decides pass/fail. Never hallucinate status codes or claim tests passed without execution proof.
- **Fail-Closed Secret Redaction**: Secrets must use `${ENV_VAR}` syntax. If an environment variable is missing, fail closed before sending requests. All sensitive headers and payload fields are automatically sanitized.
- **Immutable Run Archives**: Never overwrite previous audit runs. Every execution is stored in `api-audit/runs/run-XXX/`.

---

## Engine CLI Location

The standalone UAA engine is available globally and in-repo:
- **Windows Global**: `python "C:\Users\user\.gemini\config\skills\uaa\engine\cli.py" <subcommand> [flags]`
- **In-Workspace**: `python -m engine.cli <subcommand> [flags]`

## Reference Guides & Methodologies

The following reference documents provide deep-dive specifications for each phase:
- **6-Layer Discovery**: [discovery-layers.md](references/discovery-layers.md) — Contract, AST, route trees, plugins, runtime, gateway.
- **Request Tracing**: [request-tracing.md](references/request-tracing.md) — Auth schemas, parameters, DTO validation, and side-effects.
- **Deterministic Test Design**: [scenario-patterns.md](references/scenario-patterns.md) — 10 test categories and assertion primitives.
- **OWASP API Top 10**: [owasp-api-top10.md](references/owasp-api-top10.md) — BOLA/IDOR, broken auth, mass assignment, and data leaks.
- **Measurable Coverage Ledger**: [coverage-model.md](references/coverage-model.md) — 7-stage verification lifecycle and gap accounting.
- **Execution Safety Policy**: [execution-safety.md](references/execution-safety.md) — Non-prod target gates, fail-closed secrets, and resource bounds.
- **System Architecture**: [architecture.md](references/architecture.md) — Multi-agent adversarial challenge workflow.

---

## The 6-Phase Audit Lifecycle

### Phase 0 — Pre-flight & Safety Scope

1. Detect the repository language and web framework (FastAPI, Express, ASP.NET Core, Spring Boot, Go Gin/Chi, NestJS, etc.).
2. Determine run index: check existing runs in `api-audit/runs/` and allocate next directory (e.g. `api-audit/runs/run-001/`).
3. Identify safe non-production target base URL and environment credentials required for testing.

### Phase 1 — 6-Layer Endpoint Discovery

Reconcile routes across 6 independent sources:
1. **Layer 1: Official Contracts**: OpenAPI (`openapi.json`, `swagger.yaml`), GraphQL SDL, Proto files.
2. **Layer 2: Framework Routing**: Annotations/decorators (`@app.get`, `[HttpGet]`, `router.get`).
3. **Layer 3: AST Source Analysis**: Route trees, prefix mounts (`/api/v1`), middleware chains.
4. **Layer 4: Plugin/Dynamic Registration**: Auto-CRUD generators, modular sub-apps.
5. **Layer 5: Runtime Route Metadata**: Non-destructive route-list dumps if safe.
6. **Layer 6: Deployment & Gateways**: Ingress, reverse proxy, Nginx, Kong, Kubernetes manifests.

Reconcile into `api-audit/runs/run-XXX/endpoint-inventory.json`:
- Flag routes as `code_and_contract`, `code_only` (undocumented), `contract_only` (ghost), or `shadowed`.
- Record `endpoint_id`, method, normalized path, file anchors with line numbers, and confidence.
- Validate:
  ```bash
  python -m engine.cli validate inventory --file api-audit/runs/run-001/endpoint-inventory.json
  ```

### Phase 2 — Semantic Code Understanding

Trace each endpoint through:
- **Authentication/Authorization**: Bearer JWT, API Key, Session Cookie, Roles, Scopes, Multi-tenant `tenant_id` checks.
- **Input Validation**: DTO schemas, enums, required fields, constraints.
- **Side-Effect Classification**: `none` (idempotent read), `read`, `reversible_write`, `destructive`, `external_effect`.
- Update `endpoint-inventory.json` with parameter bindings, response models, and safety flags.

### Phase 3 — Deterministic Test Scenario Design

Generate deterministic scenarios in `api-audit/runs/run-XXX/testspecifications.json`:
- Categories: `happy_path`, `input_validation`, `auth_missing`, `auth_invalid`, `authz_forbidden`, `tenant_isolation`, `not_found`, `conflict`, `rate_limit`, `security_audit`.
- Assertions: `status`, `header_equals`, `header_exists`, `content_type`, `json_equals`, `json_exists`, `json_type`, `text_contains`, `text_not_contains`.
- Safety tagging: mark destructive scenarios with `enabled: false` and `skip_reason: "Requires explicit user confirmation"`.
- Validate:
  ```bash
  python -m engine.cli validate testspec --file api-audit/runs/run-001/testspecifications.json
  ```

### Phase 4 — Execution Gate & Deterministic Runner

**Approval Gate**: Before sending network requests, summarize the test plan to the operator:
- Target base URL: (e.g. `http://127.0.0.1:8000`)
- Endpoint count & total scenarios
- Disabled destructive/external-effect scenarios
- Request explicit confirmation to proceed.

Once approved, execute:
```bash
python -m engine.cli execute \
  --spec api-audit/runs/run-001/testspecifications.json \
  --base-url <approved_base_url> \
  --out-dir api-audit/runs/run-001/
```
Produces `execution-results.json` with evaluated assertions and redacted payloads.

### Phase 5 — Security Audit & Measurable Coverage Ledger

1. **Calculate 7-Stage Coverage Ledger**:
   ```bash
   python -m engine.cli coverage \
     --inventory api-audit/runs/run-001/endpoint-inventory.json \
     --results api-audit/runs/run-001/execution-results.json \
     --out-dir api-audit/runs/run-001/
   ```
   Ensures every unverified endpoint carries an audited reason (`destructive_action_disallowed`, `missing_credentials`, etc.).

2. **OWASP API Top 10 Security Audit**:
   ```bash
   python -m engine.cli security-check \
     --inventory api-audit/runs/run-001/endpoint-inventory.json \
     --results api-audit/runs/run-001/execution-results.json \
     --out-dir api-audit/runs/run-001/
   ```
   Evaluates BOLA/IDOR, broken authentication, mass assignment, and information leakage into `findings.json` and `findings.md`.

### Phase 6 — Interactive Reporting & Longitudinal Trends

1. **Generate Markdown Report & Standalone HTML Dashboard**:
   ```bash
   python -m engine.cli report \
     --run-dir api-audit/runs/run-001/
   ```
   Produces `report.md` and self-contained interactive `reports.html`.

2. **Regression & Historical Comparison** (if prior run exists):
   ```bash
   python -m engine.cli history-compare \
     --runs-dir api-audit \
     --prev run-001 \
     --curr run-002 \
     --out-file api-audit/runs/run-002/trend.json
   ```

3. Present the user with a concise summary linking to `reports.html` and highlighting:
   - Verified Coverage Ratio (`coverage-ledger.json`)
   - Critical/High Security Findings (`findings.md`)
   - Regressions or Fixes compared to baseline
