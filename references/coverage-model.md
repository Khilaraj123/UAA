# UAA Measurable Coverage Model

Traditional API tools rely on vanity metrics such as "100% of discovered endpoints tested". Universal API Assurance enforces a measurable verification ledger that provides continuous mathematical visibility into tested vs. untested surfaces.

## The 7-Stage Endpoint Verification Lifecycle

```
[Discovered]
     │
     ▼
[Understood]
     │
     ▼
[Scenarios Designed]
     │
     ▼
[Executed]
     │
     ▼
[Asserted]
     │
     ▼
[Verified (Passing)]  ─── OR ───>  [Unverified (With Logged Reason)]
```

### Stage 1: Discovered
The endpoint exists in at least one discovery layer (contract, route declaration, AST, plugin, runtime, gateway). Anchored with file and line range.

### Stage 2: Understood
The endpoint's request parameters, schema models, authentication requirements, and side-effect profiles have been traced and classified in `endpoint-inventory.json`.

### Stage 3: Scenarios Designed
At least one deterministic scenario exists in `testspecifications.json` targeting this endpoint.

### Stage 4: Executed
The scenario has been transmitted over the wire to the target origin by the deterministic runner.

### Stage 5: Asserted
Response code, Content-Type, headers, JSON body attributes, and negative conditions evaluated.

### Stage 6: Verified
The endpoint achieved a passing result on core functional scenarios without unexpected failures.

### Stage 7: Unverified Accounting
If an endpoint cannot be verified, it must be assigned an explicit `untested_reason`:
- `destructive_action_disallowed`: Mutation would destroy data in test environment.
- `external_effect_disallowed`: Endpoint sends real emails, SMS, or charges credit cards.
- `missing_credentials`: Required authentication token or role not provided in environment.
- `unresolved_parameter_values`: Dynamic entity ID required that cannot be created or mocked safely.
- `out_of_scope_for_run`: Explicitly excluded by user configuration.

## Quantitative Coverage Metric

The formal coverage ratio is calculated as:

$$\text{Coverage Ratio} = \frac{\text{Verified Endpoints}}{\text{Total Discovered Endpoints}}$$

An audit report never claims 100% coverage if endpoints remain unverified due to safety or missing credentials. Instead, both the verified percentage and the unverified remediation list are prominently reported.

