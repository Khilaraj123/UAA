---
name: api-security-audit
description: Identify API security vulnerabilities, business logic flaws, BOLA/IDOR, and authentication/authorization defects.
---

# API Security Audit Skill

## Mission
Conduct a rigorous security assessment of discovered endpoints and execution results. Focus on the OWASP API Security Top 10, combining static contract/code inspection with dynamic execution evidence.

## Vulnerability Focus Areas
1. **Broken Object Level Authorization (BOLA/IDOR)**:
   - Identify endpoints exposing record IDs (`/users/{id}`, `/orders/{orderId}`) without tenant ownership checks.
2. **Broken Authentication**:
   - Sensitive administrative or mutative endpoints lacking authentication decorators/middleware.
   - Weak password reset flows or unauthenticated token refresh routes.
3. **Broken Object Property Level Authorization (Mass Assignment & Excessive Data Exposure)**:
   - Endpoints binding raw request bodies directly to domain models containing sensitive fields (`role`, `is_admin`, `balance`).
   - Responses containing unnecessary internal fields (`password_hash`, `private_key`).
4. **Security Misconfiguration**:
   - Missing security headers (`X-Content-Type-Options: nosniff`, `Strict-Transport-Security`).
   - Detailed stack traces or internal runtime errors leaked in 500 responses.
5. **Rate Limiting & Resource Exhaustion**:
   - Unpaginated collection endpoints or endpoints accepting arbitrary payload sizes.

## Output Contract
Generates `findings.json` adhering to `schemas/finding.schema.json` and human-readable `findings.md`.
Every finding includes:
- `finding_id`: Stable identifier (e.g. `FIND-BOLA-001`)
- `severity`: `critical`, `high`, `medium`, `low`, `info`
- `category`: OWASP API category and CWE ID
- `evidence`: Reproducing scenario, observed request/response, code anchor
- `remediation`: Specific guidance and code diff recommendations
- `independent_review`: Review verdict by secondary reviewer agent

