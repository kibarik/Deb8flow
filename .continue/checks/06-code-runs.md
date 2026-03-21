---
name: Code Will Run
description: Проверить что код не содержит очевидных ошибок выполнения
---

Review this diff for code that will fail at runtime before any logic is executed.

Flag as FAILING if any of these are found:
- Imports or requires for modules, files, or packages that do not exist in the diff or clearly in the project
- Variables used before they are defined or outside their scope
- Function calls with wrong number of arguments compared to the function signature visible in the diff
- Type mismatches that are statically obvious: passing a string where a list is expected, calling a method that doesn't exist on that type
- Syntax that is valid in one language version but will fail in the one this project uses (e.g. walrus operator in Python 3.7, optional chaining in old Node)
- Return statements missing in functions that are clearly expected to return a value and are used as such

Flag as PASSING if the code appears syntactically and structurally sound at a static level.

Do not flag: potential runtime errors that depend on data (e.g. index out of bounds), type errors that require full inference, performance issues.
