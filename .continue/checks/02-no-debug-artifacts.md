---
name: No Debug Artifacts
description: Убрать отладочный код до отправки на review
---

Review this diff for debug artifacts left in production code.

Flag as FAILING if any of these are found outside of test files:
- print() statements in Python, console.log/console.error/console.warn in JS/TS
- Hardcoded credentials, API keys, tokens, passwords, or secrets anywhere in the code
- TODO/FIXME/HACK/XXX comments that indicate known broken or incomplete logic (not aspirational notes)
- Commented-out blocks of code larger than 3 lines
- Temporary workarounds with comments like "remove this later" or "just for testing"

Flag as PASSING if none of the above are found.

Do not flag: legitimate logging via a logging library, inline comments explaining why something works a certain way.
