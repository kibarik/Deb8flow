---
id: TASK-41
title: Создать SDD agent system prompts (Architect/DevLead/QA/Security)
status: Done
assignee: []
created_date: '2026-03-21 11:31'
updated_date: '2026-03-21 11:57'
labels:
  - sdd
  - prompts
  - debate-engine
dependencies:
  - TASK-40
references:
  - src/prompts/roles/
  - config/prompts/roles/
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Для SDD-дебатов нужны специализированные промпты 4 агентов. PRO-агент Architect защищает архитектурные решения в спецификации. CON-агенты DevLead/QA/Security — критикуют с позиции реализуемости, тестируемости и безопасности. Промпты размещаются в src/prompts/sdd/ и ссылаются из sdd_config.yaml.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 src/prompts/sdd/architect.md — PRO prompt: защита архитектурных решений, обоснование trade-offs
- [ ] #2 src/prompts/sdd/devlead.md — CON prompt: критика с позиции реализуемости, сложности, maintainability
- [ ] #3 src/prompts/sdd/qa.md — CON prompt: критика с позиции тестируемости, edge cases, observability
- [ ] #4 src/prompts/sdd/security.md — CON prompt: критика с позиции безопасности, auth, data protection, attack vectors
- [ ] #5 Каждый промпт содержит: role description, analysis focus areas, output format instructions
- [ ] #6 Промпты написаны на английском (debate engine генерирует output на языке из конфига)
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[PM-LOG] Задача выполнена в рамках TASK-40. SDD prompt файлы созданы:
- src/prompts/sdd/architect.md (PRO position, defends architectural decisions)
- src/prompts/sdd/devlead.md (CON position, critiques from implementability)
- src/prompts/sdd/qa.md (CON position, critiques from testability)
- src/prompts/sdd/security.md (CON position, critiques from security)

Все AC выполнены:
✓ Role descriptions present
✓ Analysis focus areas defined
✓ Output format instructions included
✓ Written in English

Создано при исправлении REVIEW (TASK-50), коммит e9b94df.
<!-- SECTION:NOTES:END -->
