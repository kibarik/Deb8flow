---
id: TASK-44
title: Обновить unit тесты для новой async архитектуры analyze_specification
status: To Do
assignee: []
created_date: '2026-03-21 11:32'
labels:
  - sdd
  - tests
dependencies:
  - TASK-42
  - TASK-43
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Существующие 59 тестов (test_analyze_specification.py + test_server.py) рассчитаны на синхронную версию tool без debate engine. После интеграции нужно: (1) обновить тесты под async, (2) добавить mock для DebateOrchestratorFactory чтобы unit тесты не зависели от LLM API, (3) добавить integration тест с реальным debate (отдельный marker).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Существующие тесты в test_analyze_specification.py обновлены под async (pytest-asyncio)
- [ ] #2 DebateOrchestratorFactory замокан в unit тестах — тесты не делают реальных LLM вызовов
- [ ] #3 Добавлен pytest marker @pytest.mark.integration для тестов требующих LLM API
- [ ] #4 Все unit тесты проходят без API key (mock debate output)
- [ ] #5 Coverage >= 80% для src/mcp/ модуля
<!-- AC:END -->
