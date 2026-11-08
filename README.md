# Universal API Assurance (UAA)

Autonomous, framework-agnostic, and protocol-independent API discovery, understanding, security auditing, deterministic testing, and evidence-backed assurance ecosystem.

---

## The Paradigm Shift

| Normal API Testing | AI-Powered API Testing | Universal API Assurance (UAA) |
|---|---|---|
| Executes predefined, manually authored tests. | Generates tests based on superficial endpoint signatures. | **Discovers** all 6 source layers, **understands** implementation logic, evaluates **security & correctness**, executes **deterministic tests**, and maintains a **measurable coverage ledger**. |

---

## Core Tenets

1. **Measurable Coverage Ledger**: Never trust *"discovered all 45 endpoints"*. UAA maintains a 7-stage verification ledger tracking inspected sources, discovered routes, understood logic, designed tests, executed requests, verified passes, and root-cause reasons for untested endpoints.
2. **Adversarial Agent Challenges**: Multi-agent review loops where independent agents challenge discovery completeness (Agent B), scenario rigor (Agent E), and failure consistency (Agent G).
3. **No Automatic Complete Coverage Claims**: A deep audit truthfully identifies what remains untested and provides actionable remediation.
4. **Historical Run Integrity**: Runs are archived in `api-audit/runs/run-001/`, `run-002/`. Regressions, fixes, and endpoint drift are tracked automatically across runs.
5. **Strict Architectural Separation**:
   - **Agent Skills Layer**: Autonomous reasoning, AST traversal, scenario generation, and review loops.
   - **Assurance Engine Layer**: Zero-dependency Python 3.9+ deterministic execution, secret redaction, assertions, coverage tracking, and dashboard reporting.

---

## Repository Structure

```text
universal-api-assurance/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── SECURITY.md
│
├── skills/                            # Agent Skills Layer (Reasoning & Orchestration)
│   ├── api-audit-orchestrator/SKILL.md
│   ├── api-discovery/SKILL.md & references/
│   ├── api-understanding/SKILL.md & references/
│   ├── api-test-design/SKILL.md & references/
│   ├── api-test-review/SKILL.md
│   ├── api-security-audit/SKILL.md & references/
│   ├── api-test-execution/SKILL.md
│   └── api-reporting/SKILL.md
│
├── adapters/                          # Framework & Protocol Adapters
│   ├── discovery/
│   │   ├── dotnet/                    # ASP.NET Core controllers & Minimal APIs
│   │   ├── fastapi/                   # Python FastAPI decorators & Pydantic
│   │   ├── express/                   # Express.js route & router trees
│   │   ├── nestjs/
│   │   ├── spring/
│   │   └── golang/
│   └── protocols/
│       ├── http/                      # REST / HTTP runner
│       ├── graphql/                   # GraphQL query / mutation runner
│       ├── grpc/
│       ├── websocket/
│       └── sse/
│
├── engine/                            # Assurance Engine Layer (Zero-Dependency)
│   ├── specification/                 # Canonical models & builders
│   ├── execution/                     # Deterministic runner & secret redactor
│   ├── assertions/                    # Deep JSONPath & response assertion engine
│   ├── evidence/                      # Evidence tracker & provenance model
│   ├── coverage/                      # 7-stage measurable coverage ledger
│   ├── security/                      # OWASP API Top 10 rules & analyzers
│   ├── reporting/                     # Markdown report & HTML audit dashboard
│   └── cli.py                         # Unified UAA CLI
│
├── schemas/                           # Canonical JSON Schemas (Draft 2020-12)
│   ├── endpoint.schema.json
│   ├── inventory.schema.json
│   ├── testspec.schema.json
│   ├── execution.schema.json
│   ├── finding.schema.json
│   └── coverage-ledger.schema.json
│
├── validators/                        # Schema & artifact validation tooling
│   ├── schema_validator.py
│   ├── validate_inventory.py
│   ├── validate_testspec.py
│   ├── validate_execution.py
│   └── validate_report.py
│
├── fixtures/                          # Concrete testbed applications
│   ├── dotnet/
│   ├── fastapi/
│   ├── express/
│   └── graphql/
│
├── tests/                             # Test Suite (Standard Library unittest)
│   ├── unit/                          # Models, assertions, coverage, security
│   ├── integration/                   # Mock HTTP servers, runner, multi-run history
│   ├── compatibility/                 # Framework discovery verification
│   └── end_to_end/                    # Full audit lifecycle pipeline
│
├── docs/                              # Comprehensive Documentation
│   ├── architecture.md
│   ├── execution-safety.md
│   ├── coverage-model.md
│   ├── evidence-model.md
│   └── extension-guide.md
│
└── examples/                          # Working Audit Artifacts
    ├── basic-rest/
    ├── multi-tenant-api/
    └── graphql-api/
```

---

## Quickstart

### 1. Validate All Schemas and Tests
The assurance engine uses only Python standard library:
```bash
python -m unittest discover tests
```

### 2. Validate Artifacts
```bash
python -m engine.cli validate inventory --file examples/basic-rest/endpoint-inventory.json
python -m engine.cli validate testspec --file examples/basic-rest/testspecifications.json
python -m engine.cli validate ledger --file examples/basic-rest/coverage-ledger.json
```

### 3. Execute Scenarios Against Non-Production Target
```bash
python -m engine.cli execute \
  --spec examples/basic-rest/testspecifications.json \
  --base-url http://127.0.0.1:8000 \
  --out-dir api-audit/runs/run-001/
```

### 4. Generate Coverage Ledger & Security Findings
```bash
python -m engine.cli coverage \
  --inventory examples/basic-rest/endpoint-inventory.json \
  --results api-audit/runs/run-001/execution-results.json \
  --out-dir api-audit/runs/run-001/

python -m engine.cli security-check \
  --inventory examples/basic-rest/endpoint-inventory.json \
  --results api-audit/runs/run-001/execution-results.json \
  --out-dir api-audit/runs/run-001/
```

### 5. Generate Audit Dashboard
```bash
python -m engine.cli report --run-dir api-audit/runs/run-001/
```
Open `api-audit/runs/run-001/reports.html` in any browser to explore the 6 interactive dashboard sections:
1. **Overview**: Key metrics, coverage ratio, pass rates.
2. **Endpoint Explorer**: Search, filter, and inspect discovered endpoints.
3. **Test Explorer**: Inspect requests, responses, and assertion results.
4. **Security Findings**: OWASP API Top 10 vulnerabilities, severity badges, and remediation.
5. **Failure Analysis**: Expected vs. actual diffs and root causes.
6. **Trends & Regression**: Multi-run comparisons, regressions, and verified fixes.

---

## License
Apache License 2.0. See [LICENSE](file:///d:/user/Skill/api-audit-agent-skill/LICENSE) for details.
