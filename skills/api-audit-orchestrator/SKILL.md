---
name: api-audit-orchestrator
description: Manage the complete audit lifecycle for Universal API Assurance (UAA), coordinating discovery, understanding, test generation, adversarial reviews, execution, and reporting.
---

# API Audit Orchestrator

## Mission
Orchestrate end-to-end API assurance across codebases of any language, framework, or architecture. Ensure strict multi-agent verification, maintain the measurable coverage ledger, enforce non-production execution safety gates, and manage historical audit runs.

## Multi-Agent Review Protocol (Adversarial Challenging)
The orchestrator coordinates specialized agents to challenge each other's outputs:
1. **Discovery & Verification**:
   - `Agent A (Discovery)`: Scans Layer 1–6 sources and generates `endpoint-inventory.json`.
   - `Agent B (Completeness Review)`: Independently scans AST, routes, and configs to challenge Agent A, identifying missing endpoints, shadowed routes, or uninspected sources.
2. **Understanding & Behavior**:
   - `Agent C (Understanding)`: Traces request-to-response flows, authentication, validation, and side-effects.
3. **Test Generation & Adversarial Review**:
   - `Agent D (Test Design)`: Generates deterministic `testspec.json` scenarios.
   - `Agent E (Test Review)`: Critically evaluates test completeness, missing edge cases (boundaries, auth bypass, tenant isolation), and assertion validity.
4. **Execution & Evidence**:
   - `Agent F (Deterministic Runner)`: Executes approved tests via standard library engine against approved non-production target.
5. **Security & Findings Review**:
   - `Agent G (Security & Reporting)`: Evaluates vulnerabilities (BOLA/IDOR, Broken Auth, Mass Assignment), verifies failures, calculates coverage ledger, and produces reports.

## Execution Lifecycle Stages
1. **Stage 0: Pre-flight & Safety Alignment**:
   - Establish repository root, detected languages, frameworks.
   - Verify execution safety scope (non-production base URL approval, credentials, write permissions).
   - Allocate new run ID via `RunHistoryManager` (e.g. `api-audit/runs/run-001/`).
2. **Stage 1: Discovery**:
   - Delegate to `api-discovery`. Reconcile contracts and implementations.
   - Validate inventory against `schemas/inventory.schema.json`.
3. **Stage 2: Understanding**:
   - Delegate to `api-understanding`. Map authentication, parameters, and side-effects.
4. **Stage 3: Test Design & Review**:
   - Delegate to `api-test-design` followed by `api-test-review`.
   - Validate spec against `schemas/testspec.schema.json`.
5. **Stage 4: Execution Gate**:
   - STOP for user confirmation if `--base-url` or write permissions have not been explicitly approved.
   - Delegate to `api-test-execution` using `engine.execution.runner`.
   - Validate execution output against `schemas/execution.schema.json`.
6. **Stage 5: Security & Coverage Ledger**:
   - Delegate to `api-security-audit` to detect OWASP API Top 10 vulnerabilities.
   - Run `engine.coverage.ledger` to update measurable verification ledger.
7. **Stage 6: Reporting & Historical Regression**:
   - Delegate to `api-reporting`.
   - Compare current run with previous run (`run-00X`) to identify regressions, fixes, and endpoint drift.
   - Generate `report.md` and interactive `reports.html` dashboard.

## Orchestrator Checklist
- [ ] No claim of complete coverage without coverage ledger grounding
- [ ] Explicit non-production base URL approved before executing requests
- [ ] Every run recorded in separate immutable directory (`api-audit/runs/run-XXX/`)
- [ ] Destructive / external-effect scenarios disabled by default
- [ ] Independent reviewer sign-off documented for discovery, tests, and security findings

