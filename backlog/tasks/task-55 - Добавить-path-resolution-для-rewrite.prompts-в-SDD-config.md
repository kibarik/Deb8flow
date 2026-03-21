---
id: TASK-55
title: Добавить path resolution для rewrite.prompts в SDD config
status: To Do
assignee: []
created_date: '2026-03-21 12:02'
labels:
  - sdd
  - config
  - tech-debt
dependencies:
  - TASK-46
priority: medium
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Code review выявил inconsistency: rewrite.prompts словарь существует в SddRewriteConfig но пути не резолвятся в _resolve_prompt_paths(). Нужно добавить резолюцию путей для consistency с остальными секциями.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Добавить резолюцию путей для rewrite.prompts в метод _resolve_prompt_paths()
- [ ] #2 Добавить тест для верификации что rewrite.prompts пути резолвятся корректно
<!-- AC:END -->
