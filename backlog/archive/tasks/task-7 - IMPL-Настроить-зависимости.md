---
id: TASK-7
title: '[IMPL] Настроить зависимости'
status: To Do
assignee: []
created_date: '2026-03-19 20:53'
updated_date: '2026-03-20 01:49'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Добавить poetry scripts в `pyproject.toml` для запуска MCP сервера.

**Требуемые scripts:**
```toml
[tool.poetry.scripts]
# Существующие:
product-committee = "product_committee:main"
conclusion-results = "conclusion_results:main"
rewrite = "scripts.rewrite:main"
# Новые:
sdd-mcp = "src.mcp.server:main"
```

**Шаги:**
1. Открыть `pyproject.toml`
2. Добавить script `sdd-mcp` в секцию `[tool.poetry.scripts]`
3. Добавить функцию `main()` в `src/mcp/server.py` если отсутствует
4. Выполнить `poetry install`

**Критерий завершённости:**
- PASS: `poetry run sdd-mcp --help` выполняется без ошибок
- FAIL: команда возвращает ошибку

**Сценарий демонстрации:**
1. Выполнить `poetry run sdd-mcp --help`
2. Увидеть справку или запущенный MCP сервер

**Зависимости:**
- TASK-3: mcp dependency установлена
- TASK-4: server.py создан

[SCRUM-NOTE: добавлены конкретные scripts, критерии PASS/FAIL, сценарий демонстрации, зависимости]
<!-- SECTION:DESCRIPTION:END -->
