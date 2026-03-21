---
name: Security Basics
description: Базовые проверки безопасности которые не требуют аудита
---

Review this diff for basic security issues.

Flag as FAILING if any of these are found:
- Secrets, API keys, tokens, or passwords hardcoded in source files (not in environment variable references)
- SQL queries built by string concatenation or f-string interpolation with user input
- User input passed directly to shell commands (subprocess, exec, eval) without sanitization
- New API endpoints or handlers that accept user input but have no input validation before using that input
- Sensitive data (passwords, tokens, personal information) written to logs

Flag as PASSING if none of the above are found.

Do not flag: use of environment variables for secrets, parameterized queries, validated inputs.
