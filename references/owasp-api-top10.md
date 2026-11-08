# Reference: OWASP API Security Top 10 Audit Guide

## API1:2023 - Broken Object Level Authorization (BOLA)
- **Check**: Look for route parameters identifying records (e.g. `/api/invoices/{id}`). Trace into the database query.
- **Vulnerability**: Query does `SELECT * FROM invoices WHERE id = :id` without checking `AND tenant_id = :currentUserTenantId`.
- **Remediation**: Always filter by the authenticated subject's organization / user ID.

## API2:2023 - Broken Authentication
- **Check**: Inspect route middleware. Look for routes mounted before auth middleware runs, or controllers without `[Authorize]` or `@login_required`.
- **Vulnerability**: Routes under `/admin/metrics` or `/api/export` exposed to public internet.

## API3:2023 - Broken Object Property Level Authorization
- **Check**: Compare database schema vs API response model.
- **Vulnerability**: User model contains `password_hash`, `ssn`, or `internal_flags` serialized directly into JSON.
- **Remediation**: Enforce explicit output DTOs.

## API4:2023 - Unrestricted Resource Consumption
- **Check**: Queries accepting `limit` or `page_size` parameters without max upper bound (e.g. `limit=1000000`).

## API5:2023 - Broken Function Level Authorization
- **Check**: Administrative endpoints accessible to regular authenticated users due to missing role checks.

## API6:2023 - Unrestricted Access to Sensitive Business Flows
- **Check**: Endpoints performing bulk purchases or voucher redemption without velocity/rate controls.

## API7:2023 - Server Side Request Forgery (SSRF)
- **Check**: Endpoints accepting webhooks, avatar URLs, or export callbacks fetched by the backend without internal IP filtering.

## API8:2023 - Security Misconfiguration
- **Check**: Detailed exception messages and stack traces returned in HTTP 500 error responses; missing `nosniff` headers.

