# UAA Execution Safety Policy

Ensuring automated testing does not cause data destruction, trigger unintended real-world side effects, or leak secrets is a primary design mandate of Universal API Assurance.

## 1. Non-Production Target Gates
- **Zero Production Testing**: UAA will refuse to execute tests without an explicitly provided and confirmed `--base-url`.
- **Target Origin Verification**: The runner verifies that URLs have an explicit HTTP or HTTPS scheme and valid hostname.
- **Approval Gate**: Before running test execution, the agent must ask for user confirmation specifying the exact target base URL and the authorization scope.

## 2. Secret Redaction & Fail-Closed Environment Variable Handling
- **No Hardcoded Secrets**: Test specifications must never contain raw tokens, cookies, passwords, or API keys. All credentials use `${ENV_VAR}` syntax.
- **Fail-Closed Execution**: If any required `${ENV_VAR}` is missing from the executing environment, the scenario immediately fails closed with an error before any network request is transmitted.
- **Automatic Output Redaction**:
  - Request and response headers containing `Authorization`, `Cookie`, `Set-Cookie`, `X-API-Key`, or `Proxy-Authorization` are replaced with `[REDACTED]`.
  - JSON payload keys matching `password`, `token`, `secret`, `api_key`, `access_token`, `refresh_token`, or `private_key` are recursively sanitized in all reports and logs.

## 3. Side-Effect and Destructive Mutation Protection
Every scenario is classified with a safety metadata block:
```json
{
  "safety": {
    "is_safe_read": true,
    "has_external_effects": false,
    "is_destructive": false,
    "requires_approval": true
  }
}
```

### Safety Categories:
- **`is_safe_read` (Safe)**: Idempotent GET, HEAD, or OPTIONS queries that do not mutate database records.
- **`is_destructive` (High Risk)**: DELETE, TRUNCATE, balance resets, or user deactivations. Blocked by default unless explicit `--allow-destructive` flag is supplied.
- **`has_external_effects` (High Risk)**: Endpoints triggering external services, SMS dispatch (Twilio), emails (SendGrid), or payment charges (Stripe). Automatically disabled by default.

## 4. Network and Resource Bounds
- **Timeouts**: Every request has a bounded timeout (default 10s, hard upper limit of 60s) to prevent hanging tasks.
- **Memory Protection**: Response bodies are capped at 2,000,000 bytes (2 MB). Excess bytes are truncated, and `body_truncated: true` is flagged in the report.
- **Redirect Suppression**: HTTP redirects (301, 302, 307, 308) are not followed automatically. This exposes redirect response headers directly for contract assertions and avoids accidental loops or open redirect traversal.

