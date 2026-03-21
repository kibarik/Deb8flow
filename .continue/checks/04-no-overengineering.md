---
name: No Overengineering
description: Код решает задачу, а не строит платформу для будущих задач
---

Review this diff for unnecessary complexity.

Flag as FAILING if any of these are true:
- New abstractions (base classes, interfaces, factories, registries) introduced for a single concrete use case with no existing or obvious second use case
- Generic frameworks or plugin systems built for a feature that has exactly one implementation
- More than one new layer of indirection added where the diff shows the original call chain was already clear
- Configuration options or feature flags added for behavior that is never toggled in the diff
- Code that is clearly designed for requirements not mentioned anywhere in the task description

Flag as PASSING if:
- New abstractions have at least two concrete uses visible in the diff or clearly exist already in the codebase
- Complexity added matches the complexity of the problem being solved

Do not flag: reasonable use of established patterns (repository, service layer), DRY refactoring that removes duplication.
