---
name: Edge Cases
description: Happy path написан, но где этот код сломается?
---

Review this diff and identify unhandled failure scenarios in the new code.

Flag as FAILING if any of these are unhandled and the code would silently misbehave or crash:
- null, None, undefined, or empty string/list passed to a function that does not check for it before use
- External API or network call with no timeout specified and no handling for the case where it never responds
- Division, modulo, or index access with no guard for zero or empty collection
- Async operations started in a loop or concurrently with no handling for partial failure (some succeed, some fail)
- A function that processes a list assumes it is always non-empty
- State mutation that is not safe if called concurrently when the code is used in an async or multi-threaded context
- Data from external input (user, API, file) used without checking it matches the expected shape or range

Flag as PASSING if failure scenarios are explicitly handled or the function's contract clearly documents that callers are responsible.

Do not flag: edge cases that are impossible given validated inputs upstream, performance at extreme scale unless clearly relevant.
