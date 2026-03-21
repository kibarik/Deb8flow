---
id: TASK-14
title: Implement LLM output result parser
status: Done
assignee: []
created_date: '2026-03-20 01:50'
updated_date: '2026-03-20 14:01'
labels:
  - phase-4
  - core
dependencies:
  - TASK-10
priority: high
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create src/mcp/tools/result_parser.py — parses LLM debate output into structured entities (WeakPoint[], Recommendation[], UnclearSection[]). Handles partial/malformed output gracefully.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Parses debate output into WeakPoint list with auto-generated WP-XXX IDs
- [x] #2 Parses debate output into Recommendation list with auto-generated REC-XXX IDs
- [x] #3 Parses debate output into UnclearSection list with auto-generated UNS-XXX IDs
- [x] #4 Extracts evidence snippets and confidence scores from debate reasoning
- [x] #5 Handles partial/malformed LLM output without crashing
- [x] #6 Returns empty lists (not errors) when output section is missing
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
[PM-LOG dev-started]

[DEV-LOG started | checkpoint: dev-start-TASK-14 | entire: unavailable]

[DEV-DECISION] Worktree от task-10-models | обоснование: TASK-14 зависит от TASK-10 | альтернативы: ждать merge в main

[DEV-LOG branch: task-14-parser | worktree: /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-14-parser]

[DEV-REPORT] TASK-14
Статус: CODE-REVIEW
Ветка: task-14-parser
Worktree: /Users/aleksishmanov/.superset/worktrees/dev8flow-stable/task-14-parser
PR: https://github.com/kibarik/Deb8flow/pull/new/task-14-parser
Изменены файлы: src/mcp/tools/result_parser.py, tests/test_result_parser.py
Тесты: 77 passed in 0.13s
Готово к Code Review.

[REVIEW-STATUS: approved | ready-for-testing]

[REVIEW-REPORT]
Вердикт: ОДОБРИТЬ
Итерация: #1
Review задача: TASK-36
Статус TASK-14: Done (ready-for-testing)

Все 6 AC выполнены:
- AC#1-3: WP-XXX/REC-XXX/UNS-XXX ID auto-generated
- AC#4: evidence + confidence extraction работает
- AC#5-6: graceful error handling

Следующий шаг: QA берёт в работу
<!-- SECTION:NOTES:END -->
