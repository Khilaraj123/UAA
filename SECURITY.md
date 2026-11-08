# Security Policy

## Supported Versions
Security updates are applied to the active development branch of Universal API Assurance.

| Version | Supported          |
| ------- | ------------------ |
| 2.x     | :white_check_mark: |
| 1.x     | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in Universal API Assurance, please do NOT file a public issue. Instead, report it via private security advisory or contact the maintainers directly.

## Execution Safety Guarantees

UAA implements strict safety guarantees for users running audits:
- **No Production Probing**: Execution against unspecified hosts is blocked.
- **Fail-Closed Secrets**: Test specifications referencing missing `${ENV_VAR}` variables fail closed without executing.
- **Secret Redaction**: Authorization headers, cookies, API tokens, and sensitive body fields are systematically redacted from result files, ledgers, and dashboards.
- **Destructive Mutation Guards**: `DELETE` and destructive actions are disabled unless explicitly approved with `--allow-destructive`.

