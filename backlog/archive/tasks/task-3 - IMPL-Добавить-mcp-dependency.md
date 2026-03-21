---
id: TASK-3
title: '[IMPL] Добавить mcp dependency'
status: To Do
assignee: []
created_date: '2026-03-19 20:52'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Добавить `mcp>=1.0.0` в секцию `[tool.poetry.dependencies]` файла `pyproject.toml`.

**Шаги:**
1. Открыть `pyproject.toml`
2. Добавить строку `mcp = "^1.0.0"` в секцию dependencies
3. Выполнить `poetry lock && poetry install`

**Критерий завершённости:**
- PASS: `poetry show mcp` возвращает версию >= 1.0.0
- FAIL: команда возвращает ошибку или пакет не найден

**Сценарий демонстрации:**
1. Выполнить `poetry show mcp`
2. Увидеть вывод с версией пакета

[SCRUM-NOTE: добавлены критерии PASS/FAIL, сценарий демонстрации, конкретные шаги]
<!-- SECTION:DESCRIPTION:END -->
