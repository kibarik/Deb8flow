---
name: Simplicity
description: Код понятен без комментариев и не сложнее чем нужно
---

Review this diff for unnecessary complexity and readability issues.

Flag as FAILING if any of these are true:
- A function or method does more than one clearly distinct thing and could be split without losing cohesion
- Logic requires reading more than one level of nesting (nested loops, nested conditionals, nested callbacks) when a flat version would be straightforward
- A block of code longer than ~40 lines that contains no obvious boundary where it could be decomposed
- Variable or function names that require reading the full implementation to understand what they hold or do (single letters outside loops, misleading names, generic names like "data", "result", "temp" for non-obvious values)
- The same outcome could be achieved by removing 30% or more of the new code without losing correctness or clarity
- A comment is needed to explain what the code does (not why) — the code itself should be readable

Flag as PASSING if the code is concise, each piece has a clear single responsibility, and it reads close to plain language.

Do not flag: necessary complexity that matches the inherent complexity of the problem, established verbose patterns (e.g. error handling boilerplate).
