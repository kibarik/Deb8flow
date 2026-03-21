---
name: Error Handling
description: Проверить что ошибки обрабатываются явно, а не игнорируются
---

Review this diff for error handling issues.

Flag as FAILING if any of these are true:
- A bare except/catch block that silently swallows exceptions (empty body, only pass, or only a comment)
- External I/O operations (HTTP requests, database calls, file operations) with no error handling at the call site or caller
- Async functions that call other async functions without await and without explicitly intending fire-and-forget
- Exception handlers that catch a broad base exception type but only handle one specific case, letting all others silently fail
- Error messages that expose internal stack traces or sensitive data to end users

Flag as PASSING if:
- Errors are caught and either re-raised, logged, or handled with a clear intent
- External calls have explicit handling for failure cases

Do not flag: intentional broad catches that re-raise, logging of exceptions for debugging.
