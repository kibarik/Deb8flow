---
name: Architecture Fit
description: Код вписывается в существующую архитектуру, не изобретает её заново
---

Review this diff for architectural consistency with the existing codebase visible in the diff.

Flag as FAILING if any of these are true:
- Logic that clearly belongs in one layer (e.g. database query) is placed in another (e.g. HTTP handler or UI component) when the existing codebase shows a clear separation
- A new implementation duplicates functionality that visibly exists elsewhere in the diff or is referenced from existing code (same logic, different name)
- Direct dependencies created between modules that in the rest of the codebase communicate through an interface or abstraction — breaking the existing dependency direction
- Framework or library used differently from how it is used everywhere else in the visible code (e.g. raw SQL in a project that uses an ORM, custom HTTP in a project that uses a client wrapper)
- A new pattern introduced that contradicts the established pattern for the same concern (e.g. error handling, logging, configuration access)

Flag as PASSING if the new code follows the same structural conventions as the surrounding code.

Do not flag: improvements to existing patterns when the improvement is applied consistently, necessary deviations that are clearly explained in comments.
