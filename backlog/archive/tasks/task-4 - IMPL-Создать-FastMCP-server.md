---
id: TASK-4
title: '[IMPL] Создать FastMCP server'
status: To Do
assignee: []
created_date: '2026-03-19 20:53'
updated_date: '2026-03-20 01:49'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Создать `src/mcp/server.py` с FastMCP сервером.

**Требования к серверу:**
- Имя сервера: `sdd-analyzer`
- Tool: `analyze_specification(spec_path: str)` - анализ спецификации
- Prompt: `sdd_analysis_prompt` - системный промпт для анализа

**Шаги:**
1. Создать директорию `src/mcp/`
2. Создать файл `src/mcp/server.py` с FastMCP сервером
3. Реализовать tool `analyze_specification`
4. Реализовать prompt `sdd_analysis_prompt`

**Критерий завершённости:**
- PASS: `python -m src.mcp.server` запускается без ошибок, MCP отвечает на list_tools
- FAIL: сервер не запускается или возвращает ошибки

**Сценарий демонстрации:**
1. Запустить сервер: `python -m src.mcp.server`
2. Вызвать через MCP клиент: list_tools
3. Увидеть tool `analyze_specification` в списке

**Зависимости:** TASK-3 (mcp dependency должна быть установлена)

[SCRUM-NOTE: добавлены требования к серверу, критерии PASS/FAIL, сценарий демонстрации, зависимости]
<!-- SECTION:DESCRIPTION:END -->
