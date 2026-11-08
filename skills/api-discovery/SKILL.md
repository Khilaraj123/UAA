---
name: api-discovery
description: Discover API routes, handlers, and contracts across any programming language and framework using a 6-layer source strategy and route reconciliation.
---

# API Discovery Skill

## Mission
Autonomously discover every exposed API endpoint in the target repository. Ground every discovery claim with source evidence (file path, line range, method, confidence). Reconcile differences between formal contracts and actual code implementations.

## Layered Discovery Strategy
Inspect discovery sources in strict hierarchical order:
1. **Layer 1: Official API Contracts**:
   - OpenAPI / Swagger specifications (`openapi.json`, `swagger.yaml`).
   - GraphQL schemas (`.graphql`, `.gql`, SDL definitions).
   - Protocol Buffers (`.proto` files).
   - Postman / Insomnia collections.
2. **Layer 2: Framework Route Registration**:
   - Attribute/decorator routing (e.g. C# `[HttpGet("path")]`, Python `@app.get("/path")`, Spring `@GetMapping`).
   - Imperative route registers (e.g. Express `app.use()`, `router.get()`, Go `chi.Router`, Gin `r.GET()`).
3. **Layer 3: Source-Code Analysis**:
   - AST parsing of handler functions, controller classes, and parameter bindings.
   - Route path concatenation, prefix composition, and versioning blocks (e.g. `/api/v1`).
4. **Layer 4: Dependency & Plugin Registration**:
   - Modular plugins, third-party route mount points, auto-generated CRUD routes.
5. **Layer 5: Runtime Route Metadata**:
   - Framework route dumping commands (`python -m fastapi routes`, `express-routes`, `dotnet route dump`) only when safe and pre-approved.
6. **Layer 6: Deployment & Gateway Configuration**:
   - Reverse proxy, ingress, API Gateway, Kubernetes ingress, serverless routing manifests (`serverless.yml`, `ingress.yaml`, `kong.yml`).

## Output Contract
Produces `endpoint-inventory.json` validated against `schemas/inventory.schema.json` and human-readable `endpoint-inventory.md`.

Each endpoint must record:
- `endpoint_id`: canonical identifier `[api_type]:[METHOD]:[normalized_path]`
- `api_type`: `rest`, `graphql`, `grpc`, `websocket`, etc.
- `method`: HTTP verb (GET, POST, etc.)
- `path_template`: normalized path parameter format (`/users/{id}`)
- `discovery_status`: `confirmed`, `inferred`, `contract_only`, `runtime_only`
- `confidence`: `high`, `medium`, `low`
- `source_evidence[]`: array of anchors with file path, line numbers, and snippet
- `reconciliation`: flagged as `code_and_contract`, `code_only`, `contract_only`, or `shadowed`

## Independent Discovery Verification Gate
Before handing over to `api-understanding`, Agent B must independently review the inventory:
- Are there uninspected router files in subdirectories?
- Are prefix prefixes accounted for?
- Are wildcard or regex routes expanded or documented with gaps?

