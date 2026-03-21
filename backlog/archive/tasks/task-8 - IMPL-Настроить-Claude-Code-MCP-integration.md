---
id: TASK-8
title: '[IMPL] Настроить Claude Code MCP integration'
status: To Do
assignee: []
created_date: '2026-03-19 20:53'
updated_date: '2026-03-20 01:49'
labels: []
dependencies: []
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Добавить SDD Analyzer MCP server в `.claude/mcp.json`.

**Текущее содержимое `.claude/mcp.json`:**
```json
{
  "mcpServers": {
    "backlog": {
      "command": "backlog",
      "args": ["mcp", "start"],
      "env": {
        "BACKLOG_CWD": "/Users/aleksishmanov/.superset/worktrees/dev8flow-stable/pm/mcp-.-mcp-claude-c"
      }
    }
  }
}
```

**Целевое содержимое:**
```json
{
  "mcpServers": {
    "backlog": { ...существующее... },
    "sdd-analyzer": {
      "command": "poetry",
      "args": ["run", "sdd-mcp"],
      "cwd": "/Users/aleksishmanov/.superset/worktrees/dev8flow-stable/pm/mcp-.-mcp-claude-c"
    }
  }
}
```

**Шаги:**
1. Прочитать текущий `.claude/mcp.json`
2. Добавить секцию `sdd-analyzer`
3. Записать обновлённый файл
4. Перезапустить Claude Code для активации

**Критерий завершённости:**
- PASS: Claude Code показывает `sdd-analyzer` в списке MCP серверов, tool `analyze_specification` доступен
- FAIL: сервер не появляется в списке или tool недоступен

**Сценарий демонстрации:**
1. Перезапустить Claude Code
2. Вызвать MCP tool: `sdd-analyzer__analyze_specification`
3. Получить ответ от сервера

**Зависимости:**
- TASK-4: server.py создан с tool `analyze_specification`
- TASK-7: poetry script `sdd-mcp` работает

[SCRUM-NOTE: добавлена структура mcp.json, критерии PASS/FAIL, сценарий демонстрации, зависимости]
<!-- SECTION:DESCRIPTION:END -->
