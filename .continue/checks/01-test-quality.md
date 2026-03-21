---
name: Test Quality
description: Проверить что тесты отражают реальное поведение, а не заглушки
---

Review the test files in this diff.

Flag as FAILING if any of these are true:
- More than 80% of tests mock external dependencies with zero integration or contract tests for that external system
- Test fixtures contain hardcoded data structures that clearly don't match what the real API or database would return (invented field names, wrong types, missing required fields)
- Tests only verify that a function was called, not what it returned or what effect it had
- A test passes regardless of what the implementation actually does (vacuous tests)
- There are no tests at all for new code that contains business logic

Flag as PASSING if:
- Tests verify actual outcomes, not just that mocks were called
- For external integrations, at least one test uses real response shapes (even if the HTTP call itself is mocked)
- New business logic has meaningful test coverage

Do not flag: missing 100% coverage, test file organization, naming conventions.
