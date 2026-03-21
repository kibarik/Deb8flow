---
name: Security Extended
description: Расширенные проверки безопасности — валидация, auth, утечки данных
---

Review this diff for security issues beyond hardcoded secrets (those are covered separately).

Flag as FAILING if any of these are found:
- User-controlled input used to construct a prompt sent to an LLM without sanitization (prompt injection risk)
- New endpoint or function that performs a privileged action without first checking that the caller is authenticated and authorized
- User input used directly as a filename, path, or URL component without validation (path traversal risk)
- Response or output that includes internal error details, stack traces, or system information that should not reach end users
- Data from one user returned in a context where another user could access it (missing tenant/user scoping in queries or responses)
- External input accepted and stored or processed without validating that it meets expected format, length, and type constraints

Flag as PASSING if inputs are validated, authorization is checked before action, and responses don't leak internal state.

Do not flag: issues already covered by 05-security-basics (hardcoded secrets, SQL injection, shell injection).
