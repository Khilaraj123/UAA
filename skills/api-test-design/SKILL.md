---
name: api-test-design
description: Generate deterministic, executable test specifications with assertions, authentication profiles, and safety metadata.
---

# API Test Design Skill

## Mission
Transform endpoint understanding into actionable, deterministic, and schema-compliant test scenarios. Every scenario must be reproducible, isolated, and strictly labeled with safety boundaries.

## Scenario Categories
For each endpoint, generate scenarios across applicable categories:
1. `happy_path`: Valid inputs, expected 2xx response, payload schema match.
2. `input_validation`: Missing required fields, type mismatches, boundary violations, malformed formats (expected 400 or 422).
3. `auth_missing`: Request without Authorization header (expected 401).
4. `auth_invalid`: Request with expired, forged, or malformed credentials (expected 401).
5. `authz_forbidden`: Authenticated user lacking required role/permission (expected 403).
6. `tenant_isolation`: Cross-tenant resource ID access probe (expected 404 or 403).
7. `not_found`: Non-existent resource ID (expected 404).
8. `conflict`: Duplicate unique field submission (expected 409).
9. `rate_limit`: Safe header check for rate-limiting headers (`RateLimit-Limit`, `X-RateLimit-Remaining`).
10. `security_audit`: Injection payloads, mass assignment attempts, BOLA probes.

## Assertion Kinds Supported by UAA Runner
- `status`: Check exact HTTP response status code (e.g. `200`, `401`, `422`).
- `header_equals`: Check header exact match (case-insensitive key).
- `header_exists`: Check presence of header (e.g. `X-Request-ID`).
- `content_type`: Check media type substring (e.g. `application/json`).
- `json_equals`: Check exact value at JSONPath (`data.user.id == 123`).
- `json_exists`: Verify path exists in response body.
- `json_type`: Verify data type at path (`string`, `number`, `boolean`, `array`, `object`, `null`).
- `text_contains`: Substring match in raw response body.
- `text_not_contains`: Verify pattern does NOT appear (e.g. no leaked stack traces).

## Safety & Credential Rules
- All credentials MUST use `${ENV_VAR}` syntax. Never hardcode tokens or passwords in testspecs.
- Flag `safety`:
  - `is_safe_read`: true for non-mutating requests.
  - `has_external_effects`: true if triggers external APIs/webhooks.
  - `is_destructive`: true if deletes data or causes permanent state mutation.
  - If destructive or external effect, set `enabled: false` and `skip_reason: "Requires explicit user confirmation"`.

## Output Contract
Generates `testspecifications.json` validated against `schemas/testspec.schema.json`.

