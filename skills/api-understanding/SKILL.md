---
name: api-understanding
description: Trace request-to-response behavior, data validation, authentication boundaries, and side effects through the codebase.
---

# API Understanding Skill

## Mission
Deeply trace each discovered endpoint from entry middleware down to persistence and back to response mapping. Never guess behavior based solely on endpoint path or method name: ground all understanding in code analysis.

## Request-to-Response Tracing Flow
For every endpoint in the inventory, trace:
1. **Routing & Mounting**: Route prefixes, path parameter extraction, regex constraints.
2. **Middleware Pipeline**: CORS, security headers, rate limiters, session / token extraction.
3. **Authentication & Authorization**:
   - Is auth mandatory or optional?
   - What scheme (Bearer JWT, API Key, Session Cookie, mTLS)?
   - Role / permission / scope checks (e.g. `hasRole('ADMIN')`, `[Authorize(Roles = "Manager")]`).
   - Tenant / ownership isolation: Does the handler check `resource.owner_id == current_user.id` or `WHERE tenant_id = @tenant_id`?
4. **Input Validation & Binding**:
   - Expected DTO or schema attributes.
   - Enums, minimum/maximum values, required fields, date formats.
   - Unrecognized field handling (stripped, rejected with 422/400, or accepted into dynamic map).
5. **Business Logic & Persistence**:
   - Database operations (SELECT, INSERT, UPDATE, DELETE).
   - Downstream service calls or third-party webhooks (Stripe, Twilio, SendGrid).
6. **Side Effect Classification**:
   - `none`: read-only, idempotent (e.g. GET health check, GET config).
   - `read`: reads application database with potential audit log side-effect.
   - `reversible_write`: non-destructive writes that can be reset or created with dummy keys.
   - `destructive`: hard deletes, table drops, balance deductions.
   - `external_effect`: triggers emails, SMS, real financial transactions, or external webhooks.
7. **Response Contracts & Error Handling**:
   - Documented status codes (200, 201, 204, 400, 401, 403, 404, 409, 422, 500).
   - Error format (RFC 7807 Problem Details or custom JSON).

## Output Contract
Updates `endpoint-inventory.json` with rich parameter bindings, authentication profiles, response schemas, and side effect risk classifications. Optionally generates `endpoint-details.md`.

